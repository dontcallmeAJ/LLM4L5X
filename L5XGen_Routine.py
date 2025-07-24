# L5XGen_Routine.py
import openpyxl
import re
from datetime import datetime
from L5XGen_Tag import infer_tag_types, make_tag_xml, sanitize_tag

def ProcessRoutineExcel(filepath):
    """
    Reads Column B (starting at row 2) from the first sheet of an Excel file.
    Returns the values as a newline-separated string.
    """
    try:
        wb = openpyxl.load_workbook(filepath)
        ws = wb.active
        lines = [str(cell.value) for row in ws.iter_rows(min_row=2, min_col=2, max_col=2)
                 if (cell := row[0]).value is not None]
        return "\n".join(lines)
    except Exception as e:
        return f"Error processing Excel file: {e}"

def GenerateRoutine(text: str, output_file: str = None) -> dict:
    """
    Converts IL code in string format to RSLogix 5000 Routine XML.
    Returns a dict with 'success' and 'rung_text' or 'error'.
    If output_file is given, the result is also written to disk.
    """
    routine_name = "Main_Routine"
    program_name = "Main_Program"
    controller_name = "SLMBuilt_Program"
    software_revision = "32.04"
    export_options = ("References NoRawData L5KData DecoratedData Context Dependencies "
                      "ForceProtectedEncoding AllProjDocTrans")

    def clean_line(line):
        line = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", line).strip()
        line = re.sub(r"[?]", "", line)
        return re.sub(r"\s+", " ", line)

    try:
        lines = text.splitlines()
        tags = infer_tag_types(lines)
        tag_blocks = "\n".join(make_tag_xml(t, dt) for t, dt in tags.items())

        rung_blocks = ""
        for i, line in enumerate(lines):
            cl = clean_line(line)
            if cl:
                rung_blocks += f'''<Rung Number="{i}" Type="N">
<Text>
<![CDATA[{cl}]]>
</Text>
</Rung>
'''

        now = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        rung_text = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<RSLogix5000Content SchemaRevision="1.0" SoftwareRevision="{software_revision}" TargetName="{routine_name}" TargetType="Routine" TargetSubType="RLL" ContainsContext="true" ExportDate="{now}" ExportOptions="{export_options}">
  <Controller Use="Context" Name="{controller_name}">
    <DataTypes Use="Context">
    </DataTypes>
    <Tags Use="Context">
{tag_blocks}
    </Tags>
    <Programs Use="Context">
      <Program Use="Context" Name="{program_name}">
        <Routines Use="Context">
          <Routine Use="Target" Name="{routine_name}" Type="RLL">
            <RLLContent>
{rung_blocks.strip()}
            </RLLContent>
          </Routine>
        </Routines>
      </Program>
    </Programs>
  </Controller>
</RSLogix5000Content>'''

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(rung_text)

        return {"success": True, "rung_text": rung_text}

    except Exception as e:
        return {"success": False, "error": str(e)}
