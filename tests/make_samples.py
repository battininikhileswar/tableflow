"""Generate reproducible synthetic fixtures, including known ground truth."""
import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
import fitz
ROOT=Path(__file__).resolve().parents[1]
SAMPLES=ROOT/'samples';SAMPLES.mkdir(exist_ok=True)
HEADERS=['SKU','Item','Category','Qty','Unit','Price','Tax','Discount','Total','Warehouse','Status','Date']
ROWS=[]
for i in range(1,17):
    ROWS.append([f'SKU{i:03}',f'Item {i:02}','Office',str(i+4),'Box',f'{10+i}.00','5%','0.00',f'{(10+i)*(i+4)}.00','HYD','Ready',f'2026-10-{i:02}'])

def make_pdf(path,pages,rows=None):
    c=canvas.Canvas(str(path),pagesize=landscape(A4));w,h=landscape(A4)
    for p in range(pages):
        c.setFillColorRGB(.1,.25,.21);c.setFont('Helvetica-Bold',24);c.drawString(34,h-54,'TABLEFLOW / INVENTORY')
        c.setFillColorRGB(.42,.5,.43);c.setFont('Helvetica',9);c.drawString(34,h-77,f'Synthetic extraction benchmark / 12 columns / Page {p+1} of {pages}')
        data=[HEADERS]+(rows[p*8:(p+1)*8] if rows is not None else [ROWS[p%len(ROWS)]])
        x0=34;y0=h-112;cw=(w-68)/12;rh=28
        c.setFillColorRGB(.89,.94,.83);c.rect(x0,y0-rh,cw*12,rh,fill=1,stroke=0)
        c.setStrokeColorRGB(.55,.64,.52);c.setLineWidth(.5)
        for r in range(len(data)+1): c.line(x0,y0-r*rh,x0+12*cw,y0-r*rh)
        for col in range(13): c.line(x0+col*cw,y0,x0+col*cw,y0-len(data)*rh)
        for ri,row in enumerate(data):
            c.setFillColorRGB(.13,.24,.19);c.setFont('Helvetica-Bold' if ri==0 else 'Helvetica',7)
            for ci,value in enumerate(row): c.drawString(x0+ci*cw+5,y0-ri*rh-17,value)
        c.setFont('Helvetica',8);c.setFillColorRGB(.5,.57,.49);c.drawString(34,35,'Original synthetic data. Not a real company record. First row is a header.')
        c.showPage()
    c.save()

if __name__=='__main__':
    make_pdf(SAMPLES/'sample-inventory.pdf',2,ROWS)
    doc=fitz.open(SAMPLES/'sample-inventory.pdf')
    png=doc[0].get_pixmap(matrix=fitz.Matrix(3,3),alpha=False)
    png.save(SAMPLES/'sample-scan.png')
    scanned=fitz.open()
    for source in doc:
        pix=source.get_pixmap(matrix=fitz.Matrix(3,3),alpha=False)
        page=scanned.new_page(width=source.rect.width,height=source.rect.height)
        page.insert_image(page.rect,stream=pix.tobytes('png'))
    scanned.save(SAMPLES/'sample-scanned.pdf',deflate=True);scanned.close();doc.close()
    make_pdf(SAMPLES/'sample-50-pages.pdf',50)
    (SAMPLES/'ground-truth.json').write_text(json.dumps({'headers':HEADERS,'rows':ROWS},indent=2))
