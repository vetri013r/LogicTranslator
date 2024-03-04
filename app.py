import streamlit as st
import re
import textwrap

def Rule(output, *patterns):
    "A rule that produces `output` if the entire input matches any one of the `patterns`." 
    return (output, [name_group(pat) + '$' for pat in patterns])

def name_group(pat):
    "Replace '{Q}' with '(?P<Q>.+?)', which means 'match 1 or more characters, and call it Q'"
    return re.sub('{(.)}', r'(?P<\1>.+?)', pat)

def word(w):
    "Return a regex that matches w as a complete word (not letters inside a word)."
    return r'\b' + w + r'\b'  # '\b' matches at word boundary

def match_rules(sentence, rules, defs):
    """Match sentence against all the rules, accepting the first match; or else make it an atom.
    Return two values: the Logic translation and a dict of {P: 'english'} definitions."""
    sentence = clean(sentence)
    for rule in rules:
        result = match_rule(sentence, rule, defs)
        if result: 
            return result
    return match_literal(sentence, negations, defs)

def match_rule(sentence, rule, defs):
    "Match rule, returning the logic translation and the dict of definitions if the match succeeds."
    output, patterns = rule
    for pat in patterns:
        match = re.match(pat, sentence, flags=re.I)
        if match:
            groups = match.groupdict()
            for P in sorted(groups):  # Recursively apply rules to each of the matching groups
                groups[P] = match_rules(groups[P], rules, defs)[0]
            return '(' + output.format(**groups) + ')', defs

def match_literal(sentence, negations, defs):
    "No rule matched; sentence is an atom. Add new proposition to defs. Handle negation."
    polarity = ''
    for (neg, pos) in negations:
        (sentence, n) = re.subn(neg, pos, sentence, flags=re.I)
        polarity += n * '～'
    sentence = clean(sentence)
    P = proposition_name(sentence, defs)
    defs[P] = sentence
    return polarity + P, defs

def proposition_name(sentence, defs, names='PQRSTUVWXYZBCDEFGHJKLMN'):
    "Return the old name for this sentence, if used before, or a new, unused name."
    inverted = {defs[P]: P for P in defs}
    if sentence in inverted:
        return inverted[sentence]  # Find previously-used name
    else:
        return next(P for P in names if P not in defs)  # Use a new unused name

def clean(text): 
    "Remove redundant whitespace; handle curly apostrophe and trailing comma/period."
    return ' '.join(text.split()).replace("’", "'").rstrip('.').rstrip(',')

# Rules definition (copy from your original code)
rules = [
     Rule('{P} ⇒ {Q}',         'if {P} then {Q}', 'if {P}, {Q}'),
    Rule('{P} ⋁ {Q}',          'either {P} or else {Q}', 'either {P} or {Q}'),
    Rule('{P} ⋀ {Q}',          'both {P} and {Q}'),
    Rule('～{P} ⋀ ～{Q}',       'neither {P} nor {Q}'),
    Rule('～{A}{P} ⋀ ～{A}{Q}', '{A} neither {P} nor {Q}'), # The Kaiser neither ...
    Rule('～{Q} ⇒ {P}',        '{P} unless {Q}'),
    Rule('{P} ⇒ {Q}',          '{Q} provided that {P}', '{Q} whenever {P}', 
                               '{P} implies {Q}', '{P} therefore {Q}', 
                               '{Q}, if {P}', '{Q} if {P}', '{P} only if {Q}'),
    Rule('{P} ⋀ {Q}',          '{P} and {Q}', '{P} but {Q}'),
    Rule('{P} ⋁ {Q}',          '{P} or else {Q}', '{P} or {Q}'),
]

# Negations definition (copy from your original code)
negations = [
    (word("not"), ""),
    (word("cannot"), "can"),
    (word("can't"), "can"),
    (word("won't"), "will"),
    (word("ain't"), "is"),
    ("n't", ""),  # matches as part of a word: didn't, couldn't, etc.
]

# Streamlit app
st.title("English to Logic Translator")

user_input = st.text_area("Enter an English sentence:")
if user_input:
    logic_translation, definitions = match_rules(clean(user_input), rules, {})
    
    st.markdown("### Logic Translation:")
    st.write(logic_translation)
    
    if definitions:
        st.markdown("### Definitions:")
        for P, definition in definitions.items():
            st.write(f"{P}: {definition}")
