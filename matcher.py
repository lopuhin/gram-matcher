# -*- encoding: utf-8 -*-

from copy import deepcopy
from collections import defaultdict

from pymorphy import pymorphy
from utils import some, re_compile_ui


morph = pymorphy.get_shelve_morph('ru')
words_re_core = u'[-ёа-яa-z\d]+'
punct_re_core = '|'.join('\\' + s + '(?:\s|$)' for s in '.,:;!?') + '|\.\.\.|\s-\s'
graminfo_re_core = '|'.join((u':[ёа-яa-z\d]+(?:\([ёа-яa-z\d,\?]+\)|)', '\*'))
words_re = re_compile_ui(words_re_core)
template_re = re_compile_ui(
    u'(%s)|(%s)|(%s)' % (words_re_core, graminfo_re_core, punct_re_core))

parts_of_speach = {
    u'сущ': u'С',
    u'инф': u'ИНФИНИТИВ',
    u'гл': u'Г',
    u'деепр': u'ДЕЕПРИЧАСТИЕ',
    u'прил': u'П',
    u'нар': u'Н',
    u'мест': u'МС',
    u'прмест': u'МС-П',}

norm_sig = u':норм'
match_any = '*'


def phrase_match(phrase, template):
    ''' Simple matching: phrases match if all words match.
    Return a dict of part-of-speach bingings, e.g. if template had pos tags, than
    this dict would contain a mapping from pos (with number, if there were several
    such pos in template) to words from phrase '''
    print template_re.findall(phrase)
    print template_re.findall(template)
    matches = [[some(match).strip() for match in template_re.findall(s.lower())]
               for s in (phrase, template)]
    print 'matches', matches
    if not len(matches[0]) == len(matches[1]): return False
    bindings = reduce(
        lambda bindings, (w1, w2): word_match(w1, w2, bindings),
        zip(*matches), [])
    if bindings: # recover what words matched what pos-templates
        pos_bindings = {}
        matched_pos_counts = defaultdict(int)
        for phrase_match, template_match in zip(*matches):
            if template_match.startswith(':'):
                pos = template_match.split('(', 1)[0][1:]
                pos_bindings[pos + str(matched_pos_counts[pos] + 1)] = phrase_match
                matched_pos_counts[pos] += 1
        for pos, count in matched_pos_counts.iteritems():
            if count == 1:
                pos_bindings[pos] = pos_bindings[pos + '1']
        return pos_bindings or True
    return False


def word_match(w1, w2, global_bindings=None):
    ''' Words match if they are equal, or the second is a gram description of the first,
    or the second is an asteric (*)
    Possible gram descriptions: :сущ(ср,ед,им) :норм(делать) :прил :сущ(ср,,им)
    So either a part of speach and its properties, or :норм and a normal for of word.
    We can drop some of properies, meaning that they are not important.
    Return a list of possible bindings, if match was successful and there are any '''
    if global_bindings is False: return False
    print 'considering', w1, w2
    if w2 == match_any or w1 == w2: return True
    if not any(w[0] == ':' for w in (w1, w2)): return False
    graminfo = morph.get_graminfo(w1)
    print 'graminfo', graminfo, graminfo[0]['info'], graminfo[0]['class']
    if w2.startswith(norm_sig):
        w2_norm = w2[len(norm_sig):].strip('()')
        return any(info['norm'].lower() == w2_norm for info in graminfo)
    if '(' in w2 and ')' in w2:
        w2_pos, w2_info = w2.strip(')').split('(', 1)
    else:
        w2_pos, w2_info = w2, ''
    print 'wee', w2_pos,  w2_info, parts_of_speach[w2_pos[1:]]
    if type(global_bindings) is bool or global_bindings is None:
        global_bindings = []
    new_global_bindings = []
    pos_matched, info_matched = False, False
    for info in graminfo:
        if not info['class'] == parts_of_speach[w2_pos[1:]]: continue
        pos_matched = True
        bindings = info_match(info['info'], w2_info, global_bindings)
        if not bindings: continue
        info_matched = True
        if bindings is True: continue
        # now update new_global_bindings
        for binding in bindings:
            if binding not in new_global_bindings:
                new_global_bindings.append(binding)
    if not pos_matched or not info_matched:
        return False
    return new_global_bindings or True


def info_match(info1, info2, bindings=None):
    ''' Words info match. They match if all info given in info2 matches
    with info in info1, so "1,2,3" ~ "1,,3", but not "1,2" ~ "1,2,3".
    We are also given bindings, that is a list of dicts. We must update them with
    new bindings, as they are established, or return False if it is impossible. '''
    print 'entering with bindings', bindings
    print 'infos', info1, info2
    if bindings is False: return False
    if type(bindings) is bool or bindings is None:
        bindings = []
    if not info2 or info1 == info2: return bindings or True
    splits = [info.split(',') for info in (info1, info2)]
    if len(splits[0]) < len(splits[1]): return False
    for i1, i2 in zip(*splits):
        if i2 and not i1 == i2:
            if i2[0] == '?': # it's a variable
                new_bindings = []
                for binding in bindings:
                    if i2 in binding:
                        if binding[i2] == i1:
                            new_bindings.append(binding)
                    else:
                        binding[i2] = i1
                        new_bindings.append(binding)
                if not bindings:
                    new_bindings = [{i2: i1}]
                if bindings and not new_bindings:
                    return False
                print 'new_bindings', new_bindings
                bindings = deepcopy(new_bindings)
            else:
                return False
    return bindings or True
