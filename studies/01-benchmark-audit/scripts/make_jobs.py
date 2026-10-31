import json, sys, pathlib
base = pathlib.Path(sys.argv[1]); s = json.loads((base/'results/prompts_sample.json').read_text(encoding='utf-8'))
ORIG = """You are an expert programmer. Generate clean, working code for the following request.
The code should be:
1. Syntactically correct and runnable
2. Well-commented and documented
3. Follow best practices for the language
4. Include proper error handling where appropriate
5. Be production-ready
User Request: {prompt}
Please provide only the code without explanations (unless they are code comments)."""
RELAX = """You are an expert programmer. Generate clean code for the following request.
The code should be:
1. Well-commented and documented
2. Follow best practices for the language
3. Include proper error handling where appropriate
Only use URLs or API endpoints that you are certain are real. If you are not certain, use a clearly marked placeholder such as https://api.example.com instead of guessing.
User Request: {prompt}
Please provide only the code without explanations (unless they are code comments)."""
jobs = base/'outputs/jobs'; jobs.mkdir(parents=True, exist_ok=True)
for p in s:
    for arm,(tpl,text) in {'A':(ORIG,p['prompt']),'B':(ORIG,p['swapped']),'C':(RELAX,p['prompt']),'D':(RELAX,p['swapped'])}.items():
        (jobs/f"{p['id']:03d}_{arm}.txt").write_text(tpl.replace('{prompt}',text),encoding='utf-8')
print(len(list(jobs.glob('*.txt'))),'prompt files')
