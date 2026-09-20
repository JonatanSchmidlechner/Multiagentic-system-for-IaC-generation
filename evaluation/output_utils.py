DELIMITERS = ["```hcl", "```json", "```HCL", "```Terraform", "```terraform", "```"]

def separate_answer_and_code(text, delimiters=["```hcl"]):
    for delimiter in delimiters:
        # split once at the language fence start
        parts = text.split(delimiter, 1)
        if len(parts) < 2:
            # delimiter not found, continue trying others
            continue
        # the first part is the answer
        answer = parts[0].strip()
        # take content only up to the FIRST closing fence to avoid including Evidence/JSON blocks
        rest = parts[1]
        end_idx = rest.find("```")
        code = rest[:end_idx].strip() if end_idx != -1 else rest.strip()
        if code != "":
            return answer, code
    # fallback: no fences found
    return text.strip(), ""