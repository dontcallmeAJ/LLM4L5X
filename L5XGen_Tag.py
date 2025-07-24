# L5XGen_Tag.py

import re
from collections import defaultdict

# Instruction sets by data type
BOOL_INSTR = {"XIC", "XIO", "OTE", "OTL", "OTU", "ONS"}
REAL_INSTR = {"EQ", "NE", "GE", "GT", "LE", "ADD", "SUB", "MUL", "DIV", "EQU"}
STRING_INSTR = {"FIND", "CONCAT", "INSERT", "MID", "DELETE"}
TIMER_INSTR = {"TON", "TOF", "TON.DN", "TOF.DN"}
COUNTER_INSTR = {"CTU", "CTD", "CTU.DN", "CTD.DN"}

def sanitize_tag(tag):
    """
    Replace non-word chars with underscore,
    skip tags that are only digits,
    strip leading digits if tag contains letters.
    """
    tag = re.sub(r"[^\w]", "_", tag)

    if tag.isdigit():
        return None  # skip tags only with digits

    new_tag = re.sub(r"^\d+", "", tag)
    if new_tag and re.search(r"[A-Za-z_]", new_tag):
        tag = new_tag

    return tag


def infer_tag_types(lines):
    """
    Infer tag types from instruction lines.
    Return dict {tag_name: dtype} without duplicates.
    If duplicate tag encountered, append _1, _2, ... suffix.
    """
    tag_types = {}
    tag_counts = defaultdict(int)  # track counts for duplicates
    pattern = re.compile(r"(\w+)\(([^()]+)\)")
    
    for line in lines:
        for instr, tags_str in pattern.findall(line.strip()):
            instr = instr.upper()
            if instr in BOOL_INSTR:
                dtype = "BOOL"
            elif instr in REAL_INSTR:
                dtype = "REAL"
            elif instr in STRING_INSTR:
                dtype = "STRING"
            elif instr in TIMER_INSTR:
                dtype = "TIMER"
            elif instr in COUNTER_INSTR:
                dtype = "COUNTER"
            else:
                dtype = "DINT"

            for raw_tag in map(str.strip, tags_str.split(',')):
                tag = sanitize_tag(raw_tag)
                if not tag:
                    continue
                
                base_tag = tag
                count = tag_counts[base_tag]
                # If tag already used, append suffix _1, _2, ...
                while tag in tag_types:
                    count += 1
                    tag = f"{base_tag}_{count}"
                tag_counts[base_tag] = count
                
                tag_types[tag] = dtype
    return tag_types



def make_tag_xml(tag, dtype):
    """
    Generate XML block for a tag based on its data type.
    """
    if dtype == "BOOL":
        return f'''<Tag Name="{tag}" TagType="Base" DataType="BOOL" Radix="Decimal" Constant="false" ExternalAccess="Read/Write">
  <Data Format="L5K"><![CDATA[0]]></Data>
  <Data Format="Decorated"><DataValue DataType="BOOL" Radix="Decimal" Value="0"/></Data>
</Tag>'''
    if dtype == "REAL":
        return f'''<Tag Name="{tag}" TagType="Base" DataType="REAL" Radix="Float" Constant="false" ExternalAccess="Read/Write">
  <Data Format="L5K"><![CDATA[0.00000000e+000]]></Data>
  <Data Format="Decorated"><DataValue DataType="REAL" Radix="Float" Value="0.0"/></Data>
</Tag>'''
    if dtype == "STRING":
        return f'''<Tag Name="{tag}" TagType="Base" DataType="STRING" Constant="false" ExternalAccess="Read/Write">
  <Data Format="L5K"><![CDATA[[0,'{'$00'*82}']]]></Data>
  <Data Format="String" Length="0"><![CDATA['']]></Data>
</Tag>'''
    if dtype == "DINT":
        return f'''<Tag Name="{tag}" TagType="Base" DataType="DINT" Radix="Decimal" Constant="false" ExternalAccess="Read/Write">
  <Data Format="L5K"><![CDATA[0]]></Data>
  <Data Format="Decorated"><DataValue DataType="DINT" Radix="Decimal" Value="0"/></Data>
</Tag>'''
    if dtype == "COUNTER":
        return f'''<Tag Name="{tag}" TagType="Base" DataType="COUNTER" Constant="false" ExternalAccess="Read/Write">
  <Data Format="L5K"><![CDATA[[0,0,0]]]></Data>
  <Data Format="Decorated">
    <Structure DataType="COUNTER">
      <DataValueMember Name="PRE" DataType="DINT" Radix="Decimal" Value="0"/>
      <DataValueMember Name="ACC" DataType="DINT" Radix="Decimal" Value="0"/>
      <DataValueMember Name="CU" DataType="BOOL" Value="0"/>
      <DataValueMember Name="CD" DataType="BOOL" Value="0"/>
      <DataValueMember Name="DN" DataType="BOOL" Value="0"/>
      <DataValueMember Name="OV" DataType="BOOL" Value="0"/>
      <DataValueMember Name="UN" DataType="BOOL" Value="0"/>
    </Structure>
  </Data>
</Tag>'''
    if dtype == "TIMER":
        return f'''<Tag Name="{tag}" TagType="Base" DataType="TIMER" Constant="false" ExternalAccess="Read/Write">
  <Data Format="L5K"><![CDATA[[0,0,0]]]></Data>
  <Data Format="Decorated">
    <Structure DataType="TIMER">
      <DataValueMember Name="PRE" DataType="DINT" Radix="Decimal" Value="0"/>
      <DataValueMember Name="ACC" DataType="DINT" Radix="Decimal" Value="0"/>
      <DataValueMember Name="EN" DataType="BOOL" Value="0"/>
      <DataValueMember Name="TT" DataType="BOOL" Value="0"/>
      <DataValueMember Name="DN" DataType="BOOL" Value="0"/>
    </Structure>
  </Data>
</Tag>'''

    return f"<!-- Unknown tag: {tag} -->"



