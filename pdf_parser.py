import re
import os
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
import io

class PDFParser:
    def __init__(self, filepath, tesseract_path=None, custom_rules=None):
        self.filepath = filepath
        self.tesseract_path = tesseract_path
        self.rules = {
            "question_pattern": r"(?i)^\s*(?:Question|Q|No\.?)\s*[:.]?\s*(\d+)[:.]?\s*|^\s*(\d+)\.\s+(?=[A-Za-z])",
            "choice_pattern": r"^\s*([A-F])[\.\)]\s*(.*)",
            "answer_pattern": r"(?i)(?:correct\s+)?answer\s*:\s*([A-F\s,]+)",
            "explanation_pattern": r"(?i)(?:explanation|exp)\s*:\s*(.*)",
            "passing_score": 70,
            "time_limit": 60
        }
        if custom_rules:
            self.rules.update(custom_rules)

        if self.tesseract_path:
            try:
                import pytesseract
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
            except ImportError:
                pass

    def run_ocr(self, page_image):
        if not self.tesseract_path:
            return ""
        try:
            import pytesseract
            return pytesseract.image_to_string(page_image)
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def parse_pdf(self, progress_callback=None, image_dir=None):
        import sys
        if getattr(sys, 'frozen', False):
            project_root = os.path.dirname(os.path.dirname(sys.executable))
        else:
            project_root = os.path.dirname(os.path.abspath(__file__))
            
        if not image_dir:
            image_dir = os.path.join(project_root, "cache", "images")

        # Initialize fitz and pdfplumber
        doc = fitz.open(self.filepath)
        total_pages = len(doc)
        
        # Ensure image cache directory exists
        os.makedirs(image_dir, exist_ok=True)
        
        extracted_questions = []
        current_question = None
        
        # We also attempt to extract tables using pdfplumber page by page
        plumber_doc = pdfplumber.open(self.filepath)

        # Dynamic heuristic check: does the document use explicit "Question: \d+" or "Q: \d+" tags?
        # If so, we avoid matching plain digits like "1. ", "2. " as question markers
        has_explicit_question_marker = False
        for p_idx in range(min(5, total_pages)):
            page_text = doc[p_idx].get_text("text")
            if re.search(r"(?i)\b(?:Question|Q|No\.?)\s*[:.]?\s*\d+", page_text):
                has_explicit_question_marker = True
                break

        question_pat = self.rules["question_pattern"]
        if has_explicit_question_marker:
            # Override to only match explicit question tags
            question_pat = r"(?i)^\s*(?:Question|Q|No\.?)\s*[:.]?\s*(\d+)[:.]?\s*"

        # Regex compilers
        q_re = re.compile(question_pat)
        c_re = re.compile(self.rules["choice_pattern"])
        a_re = re.compile(self.rules["answer_pattern"])
        e_re = re.compile(self.rules["explanation_pattern"])

        # Search for an Answer Key block at the end of the document
        answer_key = self._scan_for_answer_key(doc)
        
        for idx in range(total_pages):
            page = doc[idx]
            plumber_page = plumber_doc.pages[idx]
            
            # 1. Extract Text
            text = page.get_text("text")
            
            # OCR Fallback if page is scanned/empty
            if len(text.strip()) < 50 and self.tesseract_path:
                pix = page.get_pixmap(dpi=150)
                img_data = pix.tobytes("png")
                pil_img = Image.open(io.BytesIO(img_data))
                text = self.run_ocr(pil_img)
                
            # 2. Extract Images on page and create pseudo-blocks
            blocks = list(page.get_text("blocks"))
            for img_idx, img_info in enumerate(page.get_images(full=True)):
                xref = img_info[0]
                rects = page.get_image_rects(xref)
                if rects:
                    rect = rects[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Filter out tiny line dividers or spacers
                    pil_img = Image.open(io.BytesIO(image_bytes))
                    w, h = pil_img.size
                    if w < 100 or h < 60:
                        continue
                        
                    # Calculate mean brightness to filter out solid white background panels
                    import PIL.ImageStat
                    stat = PIL.ImageStat.Stat(pil_img.convert("L"))
                    mean_val = stat.mean[0]
                    if mean_val >= 245: # Solid white background panels
                        continue
                        
                    image_filename = f"img_{idx}_{img_idx}.{image_ext}"
                    image_path = os.path.join(image_dir, image_filename)
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                        
                    blocks.append((rect.x0, rect.y0, rect.x1, rect.y1, f"__IMAGE__:{image_filename}", img_idx, 1))

            # 3. Extract Tables using pdfplumber
            tables_html = ""
            tables = plumber_page.extract_tables()
            for table in tables:
                if table:
                    tables_html += self._table_to_html(table)

            # 4. Parse lines - Sort layout blocks spatially (y-coord, then x-coord)
            blocks.sort(key=lambda b: (round(b[1] / 5) * 5, b[0]))
            
            pending_images = []
            
            # Process blocks in order
            for b in blocks:
                block_text = b[4]
                block_type = b[6] if len(b) > 6 else 0
                
                if block_type == 1:
                    img_filename = block_text.split(":", 1)[1]
                    if current_question:
                        current_question["images"].append(img_filename)
                    else:
                        pending_images.append(img_filename)
                else:
                    lines = block_text.split("\n")
                    line_idx = 0
                    while line_idx < len(lines):
                        line = lines[line_idx].strip()
                        if not line:
                            line_idx += 1
                            continue
                        
                        # Check for Question match
                        q_match = q_re.match(line)
                        if q_match:
                            # Save previous question if exists
                            if current_question:
                                final_q = self._finalize_question(current_question, answer_key)
                                if final_q["question_type"] not in ["drag_drop", "fill"]:
                                    extracted_questions.append(final_q)
                            
                            q_num = q_match.group(1) or q_match.group(2)
                            q_text_start = line[q_match.end():].strip()
                            
                            current_question = {
                                "question_num": int(q_num) if q_num and q_num.isdigit() else len(extracted_questions) + 1,
                                "question_text": q_text_start,
                                "choices": [],
                                "in_choices": False,
                                "raw_choices_lines": [],
                                "correct_answers": [],
                                "explanation": "",
                                "images": list(pending_images),
                                "tables_html": tables_html,
                                "confidence": 1.0
                            }
                            pending_images.clear()
                        elif current_question:
                            # Check Choice match
                            c_match = c_re.match(line)
                            if c_match:
                                current_question["in_choices"] = True
                                letter = c_match.group(1).upper()
                                choice_text = c_match.group(2).strip()
                                current_question["choices"].append({
                                    "letter": letter,
                                    "text": choice_text
                                })
                            # Check Answer match
                            elif a_re.match(line):
                                a_match = a_re.match(line)
                                ans_str = a_match.group(1).upper()
                                # Extract letters
                                letters = re.findall(r"[A-F]", ans_str)
                                current_question["correct_answers"].extend(letters)
                            # Check Explanation match
                            elif e_re.match(line):
                                e_match = e_re.match(line)
                                current_question["explanation"] = e_match.group(1).strip()
                            else:
                                # Append to question text or choice text depending on state
                                if current_question["in_choices"] and current_question["choices"]:
                                    current_question["choices"][-1]["text"] += " " + line
                                else:
                                    current_question["question_text"] += " " + line
                        
                        line_idx += 1
            
            # Update Progress
            if progress_callback:
                progress_callback(idx + 1, total_pages)

        # Finalize the last question
        if current_question:
            final_q = self._finalize_question(current_question, answer_key)
            if final_q["question_type"] not in ["drag_drop", "fill"]:
                extracted_questions.append(final_q)
            
        plumber_doc.close()
        doc.close()
        return extracted_questions

    def _finalize_question(self, q, answer_key):
        # Determine Question Type:
        # single (MC), multiple (MR), tf (True/False), fill (Fill-in-blank)
        choices_count = len(q["choices"])
        correct_count = len(q["correct_answers"])
        
        # If no inline answer found, look in parsed answer key
        if not q["correct_answers"] and answer_key:
            ans_str = answer_key.get(q["question_num"])
            if ans_str:
                q["correct_answers"] = re.findall(r"[A-F]", ans_str.upper())
                correct_count = len(q["correct_answers"])

        # Determine type
        q_type = "single"
        if choices_count == 2 and any(c["letter"] in ["A", "B"] and c["text"].lower() in ["true", "false"] for c in q["choices"]):
            q_type = "tf"
        elif choices_count > 0:
            if correct_count > 1:
                q_type = "multiple"
            else:
                q_type = "single"
        else:
            # Check if it's a drag-and-drop question
            lower_text = q["question_text"].lower()
            if "drag" in lower_text or "drop" in lower_text or "place" in lower_text or "match" in lower_text:
                q_type = "drag_drop"
            else:
                q_type = "fill"
            
        # Format HTML for question text
        html_text = f"<p>{q['question_text'].strip()}</p>"
        
        # Add Tables if any
        if q["tables_html"]:
            html_text += q["tables_html"]
            
        # Add Images if any
        for img in q["images"]:
            # Image sources are relative to cache
            # Use block-level paragraph layout with center alignment to prevent inline float-right squishing
            html_text += f'<p align="center" style="margin: 15px 0;"><img src="cache/images/{img}" /></p>'
            
        # Format Choice mapping
        final_choices = []
        for c in q["choices"]:
            is_correct = 1 if c["letter"] in q["correct_answers"] else 0
            final_choices.append((c["letter"], c["text"].strip(), is_correct))
            
        # Check confidence
        confidence = 1.0
        if not q["correct_answers"] and q_type != "fill":
            confidence = 0.4  # Low confidence: choices exist but correct answer was not found
        elif choices_count == 0 and q_type == "fill":
            confidence = 0.7  # Moderate: fill in blank, answer might be extracted from key
            
        return {
            "question_num": q["question_num"],
            "section": "General",
            "question_text": html_text,
            "question_type": q_type,
            "choices": final_choices,
            "explanation": q["explanation"].strip() if q["explanation"] else None,
            "confidence": confidence
        }

    def _table_to_html(self, table):
        html = '<table border="1" cellpadding="5" style="border-collapse: collapse; margin: 10px 0; width: 100%; border: 1px solid #444;">'
        for r_idx, row in enumerate(table):
            html += "<tr>"
            for cell in row:
                cell_text = cell.replace("\n", " ") if cell else ""
                tag = "th" if r_idx == 0 else "td"
                html += f'<{tag} style="border: 1px solid #444; padding: 6px;">{cell_text}</{tag}>'
            html += "</tr>"
        html += "</table>"
        return html

    def _scan_for_answer_key(self, doc):
        """Scans the final pages of the PDF for an answer key/sheet."""
        answer_key = {}
        # Scan last 5 pages, or up to the full document length if smaller
        start_page = max(0, len(doc) - 5)
        
        # Patterns for matching answer keys like "1. A", "2. B", "13. C,D", "Question 5: A"
        key_patterns = [
            re.compile(r"^\s*(\d+)[\.\:]\s*([A-F](?:\s*,\s*[A-F])*)"),
            re.compile(r"^\s*(?:Question|Q)\s*(\d+)\s*[:.-]?\s*([A-F](?:\s*,\s*[A-F])*)", re.I)
        ]
        
        for p_idx in range(start_page, len(doc)):
            text = doc[p_idx].get_text("text")
            lines = text.split("\n")
            for line in lines:
                line_str = line.strip()
                for pattern in key_patterns:
                    match = pattern.match(line_str)
                    if match:
                        q_num = int(match.group(1))
                        ans = match.group(2).replace(" ", "").upper()
                        answer_key[q_num] = ans
                        break
        return answer_key
