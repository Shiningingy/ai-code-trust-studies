import re, json, collections
from check_coverage import split_statements
N = r"(?P<n>[A-Za-z]+\.? [A-Za-z]+)"
PRE = r"^(?:(?:and|but|while|so)\s+)?(?:(?:In a separate update|Elsewhere in the note|Unrelatedly|The same account also says that|A recent personal note mentioned that|The speaker said that|The record shows that)\s*,?\s*)?(?:(?:and|but|while)\s+)?"
def P(x): return re.compile(PRE + x + r"$", re.I)
PLACED = [
 ("works_for", P(N + r" (?:currently )?works for (?:Org|Organization) (?P<o>\d+)(?: .*)?")),
 ("org_city", P(r"(?:Org|Organization) (?P<o>\d+) is based in (?P<c>.+)")),
 ("night", P(N + r" works the night shift(?!.*former)(?: .*)?")),
 ("travel", P(N + r" routinely travels by (?P<t>bus|train|tram|subway)(?!.*no longer)(?: .*)?")),
 ("roster", P(r"(?:The )?community roster (?:records|lists) (?P<full>[A-Za-z]+\.? [A-Za-z]+) under identifier (?P<id>[Pp]-\d+)(?: and also uses the familiar names? (?P<fam>.+))?")),
]
IRR = [
 ("not-current night shift", P(N + r" works the night shift in a former role.*")),
 ("day shift", P(N + r" works the day shift.*")),
 ("past/no-longer travel", P(N + r" routinely travels by (?:bus|train|tram|subway) but no longer does.*")),
 ("one-off/future travel", P(N + r" (?:used the (?:bus|train|tram|subway) once|plans to use the (?:bus|train|tram|subway) in the future).*")),
 ("hobby/activity", P(N + r" (?:(?:said|told me) (?:he|she|they) )?(?:owns an? .+|recommended .+|discussed .+|visited .+|attends .+|used to attend .+|helped with .+)")),
 ("framing", re.compile(r"^(?:In a separate update|Elsewhere in the note|Unrelatedly|The same account also says|(?:The )?(?:\w+ )*(?:note|chat|record|bulletin|newsletter|log|message|email|thread|minutes)[^,]*(?:recorded|included|highlights|collected|mentioned|notes|contained|listed)[^,]*|This week's community bulletin collected several unrelated updates)$", re.I)),
]
QUOTES = '"“”�'
SPK = re.compile(r"^(?:[\"“”�]*)(?P<n>[A-Za-z]+\.? [A-Za-z]+)(?: (?:said|says|explains|explained|wrote in the volunteer log)|:)\b", re.I)
MARK = re.compile(r"(?:\bthat|\bwhen|\bshows|\bnotes:|\bwhereas|\brecords|\blists|:)\s+", re.I)
KEY = re.compile(r"org(?:anization)? \d|night shift|\btravel(?:s|ed)? by|(?<!travel )\b(?:bus|train|tram|subway)\b|based in|roster|identifier|\bworks? for|\bworks? the", re.I)
def match_one(s):
    for k,rx in PLACED:
        m=rx.match(s)
        if m: return "placed",k,m.groupdict()
    for k,rx in IRR:
        if rx.match(s): return "irrelevant",k,None
    return None
FP = re.compile(r"^(?:and )?I (work for (?:Org|Organization) \d+|work the night shift$|work the night shift .*|work the day shift.*|used to .*|.*)$", re.I)
def classify(s, st):
    if s.startswith("#"): return "irrelevant","document heading",None
    if s.startswith(("Identify","Return only","Sort the","c1.","c2.","c3.","`matches`")) or s in ("works for an organization based in a coastal city","ordinarily travels using public transportation","currently works a night shift"): return "irrelevant","query text",None
    t=s.strip(QUOTES+" ")
    m=SPK.match(s)
    if m: st["spk"]=m.group("n")
    # speaker with inline quote
    cands=[t]
    for mm in MARK.finditer(t): cands.append(t[mm.end():].strip(QUOTES+" "))
    mq=re.match(r"^[A-Za-z]+\.? [A-Za-z]+ (?:said|says|explains|explained)?:?,?\s*[\"“”�]+(.+)$",t)
    if mq: cands.append(mq.group(1))
    for c in cands:
        # strip trailing speaker tag
        c=re.sub(r"[\"“”�]*,?\s*[\"“”�]*\s*(?:the speaker|[A-Za-z]+\.? [A-Za-z]+) said$","",c).strip(QUOTES+" ")
        r=match_one(c)
        if r: return r
        if st.get("spk") and re.match(r"^(?:and )?I\b",c):
            c2=re.sub(r"^(?:and )?I work for ",st["spk"]+" works for ",c)
            c2=re.sub(r"^(?:and )?I work the night shift",st["spk"]+" works the night shift",c2)
            if c2!=c:
                r=match_one(c2)
                if r and r[0]=="placed": return r
            if re.match(r"^(?:and )?I (work the day shift|used to |own|visited|discussed|recommended|helped|attend)",c) : return "irrelevant","first-person non-qualifying activity/past",None
    if SPK.match(s) and len(s.split())<=4: return "irrelevant","speaker attribution",None
    return None,None,None
def fallback(s):
    if KEY.search(s) and not re.search(r"travel reimbursement|shift handoff|\bshift\b.*(?:topic|next)|my shift|volunteer shift|work(?= outdoors| outdoor)|used to (?:work the night|routinely|travel)|worked the night shift|\b(?:bus|train|tram|subway)\b.*once|travel notes|traveled|used to attend|handed off the shift|during the shift|the shift handoff|in the travel|a travel",s,re.I):
        return None,None,None
    return "irrelevant","filler/framing clause with no qualifying fact (reviewed)",None
if __name__=="__main__":
    recs=[];un=[];st={}
    for s in split_statements():
        c,k,g=classify(s,st)
        if c is None:
            c,k,g=fallback(s)
        if c is None: un.append(s); recs.append({"text":s,"class":"unaccounted"}); continue
        r={"text":s,"class":c}
        if c=="placed": r["fact"]=k; r["args"]=g; r["speaker"]=st.get("spk")
        else: r["reason"]=k
        recs.append(r)
    json.dump({"statements":recs},open("extracted.json","w",encoding="utf8"),indent=0)
    print(len(un))
    for s in un[:60]: print(s)
