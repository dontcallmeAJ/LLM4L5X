# Validator_InstructionDetection.py

import re

instruction_keywords = {
    'TON': ['ON Timer','timer on', 'on delay timer', 'TON', 'TOn','ToN', 'time delay on', 'time on', 'timer start', 'turn on after delay',
            'wait for time', 'wait until time', 'time delay', 'time starts', 'start timer', 'timed start', 'ON-delay'],
    'TOF': ['Off Timer', 'timer off', 'off delay timer', 'TOF', 'ToF', 'time delay off', 'time off', 'timer stop', 'turn off after delay',
            'wait for off time', 'wait until off', 'timer stops', 'start timer off', 'time stops', 'OFF-delay'],
    'CTD': ['counter down', 'count down', 'CTD', 'decrement counter', 'decrease count', 'count decrease', 'count fall',
            'subtract from counter', 'decrease value', 'count reduction', 'counting down', 'down counting'],
    'CTU': ['count', 'counter', 'counter up', 'count up','counting up', 'CTU', 'count increments', 'increment counter', 'increase count', 'count rise',
            'add to counter', 'count event', 'increase value', 'up counting'],
    'ONS': ['ons','one shot', 'pulse', 'single trigger', 'on first press', 'one shot on rising edge', 'goes from 0 to 1', 'one-shot rising edge'],
    'ADD': ['add', 'sum', 'total', 'plus', 'combine', 'addition', '+', 'added'],
    'SUB': ['subtract', 'minus', 'reduce', 'sub', 'subtracted', 'subtraction', '-', 'difference'],
    'MUL': ['mul','multiply', 'product', 'times', '*', 'multiplied', 'multiplication'],
    'DIV': ['div','divide', 'quotient', 'division', '/', 'divided'],
    'EQ': ['equal', 'equals', '==', 'same', 'equality'],
    'NE': ['not equal', 'not equals', '!=', 'different', 'differs', 'inequality', 'not same'],
    'GE': ['geq','greater than or equal', '>='],
    'GT': ['gt','greater than', '>', 'more than', 'exceeds'],
    'LE': ['less than or equal', '<='],
    'LT': ['less than', '<', 'smaller than', 'is below'],
    'MOV': ['mov','move', 'transfer', 'assign'],
    'COP': ['cop','copy', 'duplicate', 'replicate'],
    'CLR': ['clr','clear', 'erase', 'empty', 'wipe'],
    'XIC': ['xic','is on', 'is active','is activated', 'is enabled', 'is high', 'is true', 'is pressed', 'is energized', 'is selected', 'is running', 'is triggered', 'is open', 'is set to ON', 'is set to 1', 'is set to True', 'is set to High', 'is set High'],
    'XIO': ['xio','is off', 'is not active','is not activated', 'is de-activated', 'is disabled', 'is low', 'is false', 'is not pressed', 'is de-energized', 'is not energized', 'is not selected', 'is stopped', 'is not triggered', 'is close', 'is set to OFF', 'is set to False', 'is set to Low', 'is set Low'],
    'OTU': ['otu','unlatch', 'release', 'unlock', 'reset', 'disable', 'de-energize', 'de-activate', 'turn off', 'switch off', 'set to off', 'stop', 'close', 'trigger off'],
    'OTE': ['ote','Trigger output on', 'energize', 'activate', 'enable', 'turn on', 'switch on', 'set to on', 'run', 'open', 'trigger on', 'set true', 'set 1'],
    'OTL': ['otl','latch', 'latched state', 'hold']
}

instruction_operand_counts = {
    'ADD': 3, 'SUB': 3, 'MUL': 3, 'DIV': 3,
    'EQ': 2, 'NE': 2, 'GE': 2, 'GT': 2, 'LE': 2, 'LT': 2,
    'MOV': 2, 'COP': 3, 'CLR': 1,
    'OTE': 1, 'OTL': 1, 'OTU': 1, 'ONS': 1,
    'XIC': 1, 'XIO': 1,
    'TON': 3, 'TOF': 3, 'CTD': 3, 'CTU': 3
}

preferred_order = [
    'ONS', 'CTD', 'CTU', 'TON', 'TOF',  
    'GE', 'NE', 'LE', 'EQ', 'GT', 'LT',
    'MOV', 'COP', 'CLR',
    'XIC', 'XIO',
    'OTU', 'OTL', 'OTE','ADD', 'SUB', 'MUL', 'DIV'
]

def detect_instruction(question: str):

    found_keywords = []
    matched_instruction = None
    question_lower = question.lower()

    # Prioritized keyword search
    for instruction in preferred_order:
        keywords = [k.lower() for k in instruction_keywords.get(instruction, [])]
        sorted_keywords = sorted(keywords, key=lambda k: -len(k))  # longest match first
        for kw in sorted_keywords:
            if kw.isalnum():
                pattern = r'\b' + re.escape(kw) + r'\b'
            else:
                pattern = re.escape(kw)
            if re.search(pattern, question_lower):
                found_keywords.append(kw)
                matched_instruction = instruction
                operand_count = instruction_operand_counts.get(instruction)
                return found_keywords, matched_instruction, operand_count

    if ('value' in question_lower and 
    ('assign' in question_lower or 'set' in question_lower)):
        found_keywords.append('assign/set value')
        matched_instruction = 'MOV'
        operand_count = instruction_operand_counts.get('MOV')
        return found_keywords, matched_instruction, operand_count

    if re.search(r'(?=.*\btimer\b)(?=.*\brising\s+(scan|pulse|edge)\b)', question_lower):
        found_keywords.append('Timer on rising scan')
        matched_instruction = 'TON'
        operand_count = instruction_operand_counts.get('TON')
        return found_keywords, matched_instruction, operand_count

    if re.search(r'(?=.*\btimer\b)(?=.*\bfalling\s+(scan|pulse|edge)\b)', question_lower):
        found_keywords.append('Timer on falling scan')
        matched_instruction = 'TOF'
        operand_count = instruction_operand_counts.get('TOF')
        return found_keywords, matched_instruction, operand_count

    if re.search(r'\breset\b.*\bto\s+(0|zero)\b', question_lower):
        found_keywords.append('reset to 0 or zero')
        matched_instruction = 'CLR'
        operand_count = instruction_operand_counts.get('CLR')
        return found_keywords, matched_instruction, operand_count

    timer_not_done_pattern = r"\btimer\b.*\b(not|no|n't|isn't|hasn't|haven't)\b.*\b(done|completed|reached)\b"
    timer_not_done_match = re.search(timer_not_done_pattern, question_lower)
    if timer_not_done_match:
        found_keywords.append('timer not done')
        matched_instruction = 'XIO' 
        operand_count = 1
        return found_keywords, matched_instruction, operand_count

    counter_not_done_pattern = r"\bcounter\b.*\b(not|no|n't|isn't|hasn't|haven't)\b.*\b(done|completed|reached)\b"
    counter_not_done_match = re.search(counter_not_done_pattern, question_lower)
    if counter_not_done_match:
        found_keywords.append('counter not done')
        matched_instruction = 'XIO'  
        operand_count = 1
        return found_keywords, matched_instruction, operand_count
    
    timer_done_pattern = r'\btimer\b.*\b(reached|completed|done)\b'
    timer_done_match = re.search(timer_done_pattern, question_lower)
    if timer_done_match:
        found_keywords.append('timer done')
        matched_instruction = 'XIC'  
        operand_count = 1
        return found_keywords, matched_instruction, operand_count
    
    counter_done_pattern = r'\bcounter\b.*\b(reached|completed|done)\b'
    counter_done_match = re.search(counter_done_pattern, question_lower)
    if counter_done_match:
        found_keywords.append('counter done')
        matched_instruction = 'XIC' 
        operand_count = 1
        return found_keywords, matched_instruction, operand_count

    return found_keywords, None, None

