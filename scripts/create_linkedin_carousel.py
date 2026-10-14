from pathlib import Path

from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "AutoSTAIR_LinkedIn_Carousel.pdf"
W = H = 1080

INK = HexColor("#172132")
MUTED = HexColor("#647084")
PAPER = HexColor("#F4F0E7")
CARD = HexColor("#FFFDF8")
ORANGE = HexColor("#F26A3D")
CYAN = HexColor("#3FB8C5")
NAVY = HexColor("#18263D")
WHITE = HexColor("#FFFFFF")
LINE = HexColor("#DED8CC")


def bg(c, color=PAPER):
    c.setFillColor(color)
    c.rect(0, 0, W, H, fill=1, stroke=0)


def label(c, text, x=74, y=990, color=ORANGE):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(x, y, text.upper())


def footer(c, page, dark=False):
    c.setFillColor(HexColor("#C7CED8") if dark else MUTED)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(74, 46, "AUTOSTAIR / RAG BENCHMARK")
    c.drawRightString(W - 74, 46, f"{page:02d} / 10")


def wrap(c, text, x, y, max_width, font="Helvetica", size=30, leading=40, color=INK, max_lines=None):
    words = text.split()
    lines, line = [], ""
    for word in words:
        trial = word if not line else line + " " + word
        if stringWidth(trial, font, size) <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    if max_lines:
        lines = lines[:max_lines]
    c.setFillColor(color)
    c.setFont(font, size)
    for i, item in enumerate(lines):
        c.drawString(x, y - i * leading, item)
    return y - len(lines) * leading


def title(c, text, y=900, size=62, color=INK, width=900):
    return wrap(c, text, 74, y, width, "Helvetica-Bold", size, size * 1.06, color)


def rounded(c, x, y, w, h, fill=CARD, stroke=LINE, r=20):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(1.4)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1)


def metric_bar(c, name, value, y, color):
    c.setFont("Helvetica-Bold", 23)
    c.setFillColor(INK)
    c.drawString(110, y, name)
    c.setFillColor(HexColor("#E6E0D6"))
    c.roundRect(245, y - 2, 600, 23, 11, fill=1, stroke=0)
    c.setFillColor(color)
    c.roundRect(245, y - 2, 600 * value, 23, 11, fill=1, stroke=0)
    c.setFillColor(INK)
    c.drawRightString(950, y, f"{value:.2f}")


def page1(c):
    bg(c, NAVY)
    label(c, "A resource-light RAG benchmark", color=ORANGE)
    wrap(c, "Does document structure improve RAG?", 74, 875, 820, "Helvetica-Bold", 82, 85, WHITE)
    wrap(c, "AutoSTAIR compares ordinary chunk retrieval with an index-guided pipeline on one long public report.", 78, 575, 720, "Helvetica", 31, 43, HexColor("#D6DCE5"))
    c.setFillColor(ORANGE); c.circle(895, 265, 105, fill=1, stroke=0)
    c.setFillColor(CYAN); c.circle(755, 198, 45, fill=1, stroke=0)
    c.setStrokeColor(WHITE); c.setLineWidth(16); c.line(560, 360, 948, 180)
    footer(c, 1, True)


def page2(c):
    bg(c); label(c, "The question")
    title(c, "A document already has a map. Should RAG use it?")
    wrap(c, "Most RAG pipelines split text into equal-sized chunks and search everything at once. Long reports and books already contain human-authored structure: chapters, headings, and an index.", 74, 650, 900, "Helvetica", 31, 43, MUTED)
    rounded(c, 74, 230, 932, 225)
    c.setFillColor(INK); c.setFont("Helvetica-Bold", 28); c.drawString(112, 395, "Objective")
    wrap(c, "Measure whether routing through that structure improves retrieval and final answer quality under a controlled setup.", 112, 342, 820, "Helvetica-Bold", 34, 44, INK)
    footer(c, 2)


def page3(c):
    bg(c); label(c, "Research inspiration")
    title(c, "IBM Research's STAIR paper")
    wrap(c, "STAIR predicts the relevant leaf section from a question and the document's full table of contents. It also introduces SearchTome, a benchmark built from 18 books across six domains.", 74, 700, 900, "Helvetica", 31, 43, MUTED)
    rounded(c, 74, 305, 932, 250, fill=NAVY, stroke=NAVY)
    wrap(c, "Our project asks a smaller, practical question. We use existing document structure directly, without training a retriever or generating a new hierarchy.", 112, 485, 820, "Helvetica-Bold", 34, 45, WHITE)
    c.setFillColor(ORANGE); c.rect(74, 170, 310, 16, fill=1, stroke=0)
    wrap(c, "Inspired by the paper, not a reproduction of it.", 74, 140, 800, "Helvetica-Bold", 23, 30, INK)
    footer(c, 3)


def page4(c):
    bg(c); label(c, "The test bed")
    title(c, "One public report. Two retrieval routes.")
    stats=[("276","pages"),("395","chunks"),("54","authored sections"),("20","questions")]
    for i,(n,s) in enumerate(stats):
        x=74+(i%2)*470; y=610-(i//2)*245
        rounded(c,x,y,432,190)
        c.setFillColor(ORANGE if i in (0,3) else CYAN); c.setFont("Helvetica-Bold",58); c.drawString(x+32,y+95,n)
        c.setFillColor(MUTED); c.setFont("Helvetica-Bold",22); c.drawString(x+34,y+50,s.upper())
    wrap(c, "Source: World Bank, World Development Report 2024: The Middle-Income Trap.", 74, 180, 900, "Helvetica", 25, 34, MUTED)
    footer(c, 4)


def page5(c):
    bg(c, NAVY); label(c, "Controlled design")
    title(c, "Same evidence and models. Different route.", color=WHITE)
    boxes=[("FLAT RAG","Question -> search all 395 passages -> answer",CYAN), ("INDEX-GUIDED RAG","Question -> select 1 of 54 sections -> search within it -> answer",ORANGE)]
    for i,(h,t,col) in enumerate(boxes):
        y=565-i*260
        rounded(c,74,y,932,205,fill=HexColor("#22324C"),stroke=col)
        c.setFillColor(col); c.setFont("Helvetica-Bold",22); c.drawString(112,y+144,h)
        wrap(c,t,112,y+95,820,"Helvetica-Bold",32,42,WHITE)
    footer(c, 5, True)


def page6(c):
    bg(c); label(c, "Retrieval results")
    title(c, "Structure helped at rank one.")
    c.setFillColor(CYAN); c.circle(90, 696, 10, fill=1, stroke=0); c.setFillColor(INK); c.setFont("Helvetica-Bold",20); c.drawString(112,688,"Index-guided")
    c.setFillColor(ORANGE); c.circle(315, 696, 10, fill=1, stroke=0); c.setFillColor(INK); c.drawString(337,688,"Flat")
    labels=["Hit@1","Hit@3","Hit@5","MRR"]
    structured=[.60,.80,.80,.70]; flat=[.55,.85,.90,.6958]
    for i,n in enumerate(labels):
        y=605-i*115
        c.setFillColor(INK); c.setFont("Helvetica-Bold",21); c.drawString(82,y+26,n)
        c.setFillColor(HexColor("#E6E0D6")); c.roundRect(195,y+34,690,18,9,fill=1,stroke=0); c.setFillColor(CYAN); c.roundRect(195,y+34,690*structured[i],18,9,fill=1,stroke=0); c.setFillColor(INK); c.drawRightString(965,y+31,f"{structured[i]:.2f}")
        c.setFillColor(HexColor("#E6E0D6")); c.roundRect(195,y-4,690,18,9,fill=1,stroke=0); c.setFillColor(ORANGE); c.roundRect(195,y-4,690*flat[i],18,9,fill=1,stroke=0); c.setFillColor(INK); c.drawRightString(965,y-7,f"{flat[i]:.2f}")
    wrap(c,"Flat search recovered more relevant evidence at depth: Hit@5 reached 0.90 vs 0.80.",74,150,900,"Helvetica-Bold",27,36,INK)
    footer(c, 6)


def page7(c):
    bg(c); label(c, "Manual answer review")
    title(c, "More wins did not mean a higher average score.")
    items=[("8","index-guided wins",CYAN),("6","flat wins",ORANGE),("6","ties",INK)]
    for i,(n,s,col) in enumerate(items):
        x=74+i*315
        rounded(c,x,575,286,170)
        c.setFillColor(col); c.setFont("Helvetica-Bold",54); c.drawString(x+28,660,n)
        c.setFillColor(MUTED); c.setFont("Helvetica-Bold",17); c.drawString(x+28,615,s.upper())
    rounded(c,74,285,445,205,fill=NAVY,stroke=NAVY); rounded(c,561,285,445,205,fill=CARD,stroke=LINE)
    c.setFillColor(WHITE); c.setFont("Helvetica-Bold",56); c.drawString(110,390,"4.85 / 5"); c.setFont("Helvetica-Bold",20); c.drawString(112,345,"FLAT OVERALL QUALITY")
    c.setFillColor(INK); c.setFont("Helvetica-Bold",56); c.drawString(598,390,"4.61 / 5"); c.setFont("Helvetica-Bold",20); c.drawString(600,345,"INDEX-GUIDED QUALITY")
    wrap(c,"Blinded review: correctness, grounding, completeness, and citation quality.",74,205,900,"Helvetica",23,31,MUTED)
    footer(c, 7)


def page8(c):
    bg(c); label(c, "Why the result is mixed")
    title(c, "The section decision can become a bottleneck.")
    rounded(c,74,535,932,235,fill=NAVY,stroke=NAVY)
    c.setFillColor(CYAN); c.setFont("Helvetica-Bold",23); c.drawString(112,700,"WHEN ROUTING WORKED")
    wrap(c,"The evidence was focused, direct, and easier to audit.",112,642,820,"Helvetica-Bold",35,46,WHITE)
    rounded(c,74,250,932,235,fill=CARD,stroke=ORANGE)
    c.setFillColor(ORANGE); c.setFont("Helvetica-Bold",23); c.drawString(112,415,"WHEN ROUTING FAILED")
    wrap(c,"The correct passage was outside the selected section, so the second stage could not recover it.",112,357,820,"Helvetica-Bold",34,45,INK)
    wrap(c,"Two cross-section questions produced safe abstentions instead of answers.",74,182,900,"Helvetica",24,33,MUTED)
    footer(c, 8)


def page9(c):
    bg(c); label(c, "How this differs from STAIR")
    title(c, "A benchmark of layouts, not a trained retriever.")
    points=[("No fine-tuning","We compare practical retrieval pipelines using existing embeddings and generation."),("One public report","STAIR evaluates 18 books across six domains; this is a deliberately small case study."),("End-to-end RAG","We examine both retrieval metrics and the quality of cited answers."),("Existing structure","We preserve the report's authored sections instead of creating a hierarchy with AI.")]
    for i,(h,t) in enumerate(points):
        y=690-i*145
        c.setFillColor(ORANGE if i%2==0 else CYAN); c.circle(94,y+18,13,fill=1,stroke=0)
        c.setFillColor(INK); c.setFont("Helvetica-Bold",27); c.drawString(130,y+4,h)
        wrap(c,t,130,y-38,820,"Helvetica",21,29,MUTED)
    footer(c, 9)


def page10(c):
    bg(c, ORANGE); label(c, "Main takeaway", color=INK)
    wrap(c,"Use structure as a strong routing signal, with a global fallback.",74,870,900,"Helvetica-Bold",67,72,INK)
    wrap(c,"A hybrid design can keep the focus of index-guided retrieval without losing evidence when the first section choice is wrong.",78,560,860,"Helvetica",31,43,HexColor("#3F281E"))
    c.setFillColor(INK); c.roundRect(74,230,932,160,22,fill=1,stroke=0)
    wrap(c,"Small study. Useful signal. Clear next experiment.",112,332,820,"Helvetica-Bold",35,45,WHITE)
    c.setFillColor(INK); c.setFont("Helvetica-Bold",20); c.drawString(74,145,"FULL METHODOLOGY, CODE, AND RESULTS IN THE POST")
    footer(c, 10)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
    c.setTitle("AutoSTAIR LinkedIn Carousel")
    c.setAuthor("Arsalan Ahmed")
    c.setSubject("A controlled benchmark of flat and index-guided retrieval-augmented generation")
    for page in (page1,page2,page3,page4,page5,page6,page7,page8,page9,page10):
        page(c); c.showPage()
    c.save()
    print(OUT)


if __name__ == "__main__":
    main()
