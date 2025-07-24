# L5XGen_Rung.py

import re
from datetime import datetime
from L5XGen_Tag import infer_tag_types, make_tag_xml, sanitize_tag

def clean_line(line):
    line = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", line).strip()
    line = re.sub(r"[?]", "", line)
    return re.sub(r"\s+", " ", line)

def GenerateRung(text: str) -> dict:
    """
    Converts IL code in string format to a valid RSLogix 5000 Rung XML snippet.
    Returns a dictionary with 'success' and 'rung_text' or 'error'.
    """

    # === Configurable variables ===
    routine_name = "Main_Routine"
    program_name = "Main_Program"
    controller_name = "SLMBuilt_Program"
    software_revision = "32.04"
    export_options = ("References NoRawData L5KData DecoratedData Context "
                      "RoutineLabels AliasExtras IOTags NoStringData "
                      "ForceProtectedEncoding AllProjDocTrans")

    try:
        lines = text.splitlines()
        tags = infer_tag_types(lines)
        tag_blocks = "\n".join(make_tag_xml(t, dt) for t, dt in tags.items())

        rung_blocks = ""
        for line in lines:
            cl = clean_line(line)
            if cl:
                rung_blocks += f'''<Rung Use="Target" Number="0" Type="N">
<Text><![CDATA[{cl}]]></Text>
</Rung>
'''

        now = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
        rung_text = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<RSLogix5000Content SchemaRevision="1.0" SoftwareRevision="{software_revision}" TargetType="Rung" TargetCount="1" ContainsContext="true" ExportDate="{now}" ExportOptions="{export_options}">
<Controller Use="Context" Name="{controller_name}">
<DataTypes Use="Context"/>
<Tags Use="Context">
{tag_blocks}
</Tags>
<Programs Use="Context">
<Program Use="Context" Name="{program_name}">
<Routines Use="Context">
<Routine Use="Context" Name="{routine_name}">
<RLLContent Use="Context">
{rung_blocks.strip()}
</RLLContent>
</Routine>
</Routines>
</Program>
</Programs>
</Controller>
</RSLogix5000Content>
'''
        return {"success": True, "rung_text": rung_text}

    except Exception as e:
        return {"success": False, "error": str(e)}
