# -*- encoding: utf-8 -*-

import unittest

import matcher


class TestMatcher(unittest.TestCase):
    def test_word_matching(self):
        for word, template in (
            (u'чтототакое', '*'),
            (u'просто', u'просто'),
            (u'слово', u':сущ(ср,ед,им)'),
            (u'слово', u':сущ(,ед,им)'),
            (u'слово', u':сущ(,ед)'),
            (u'слово', u':сущ(,ед,)'),
            (u'делать', u':инф(дст)'),
            (u'делать', u':инф'),
            (u'делая', u':норм(делать)'),):
            print word, template
            self.assert_(matcher.word_match(word, template))
        for word, template in (
            (u'делая', u':норм'),):
            self.assert_(not matcher.word_match(word, template))

    def test_word_binding_matching(self):
        for word, template, bindings in (
            (u'слово', u':сущ(ср,?x,им)', [{'?x': u'ед'}]),
            (u'слово', u':сущ(ср,ед,?y)', [{'?y': u'им'}, {'?y': u'вн'}]),
            (u'слово', u':сущ(?x,ед,?y)', [{'?x': u'ср', '?y': u'им'},
                                           {'?x': u'ср', '?y': u'вн'}]),
            ):
            print word, template, bindings
            self.assert_(bindings == matcher.word_match(word, template))

    def test_phrase_matching(self):
        for phrase, template in (
            (u'Я пошел гулять!', u'Я :гл(дст,прш,мр,ед) :инф(дст)!'),
            (u'Кто-то, взял ключ',
             u':мест(мр,ед,им), :гл(дст,прш,мр,ед) :сущ(мр,ед,им)'),
            (u'что такое?', u'* *?'),
            (u'что такое?', u'* * *'),
            (u'Я пошел гулять!', u':мест :гл :инф!'),
            ):
            print phrase, '|', template
            self.assert_(matcher.phrase_match(phrase, template))
        for phrase, template in (
            (u'Я пойду гулять!', u'Я :гл(дст,прш,мр,ед) :инф(дст)'),
            (u'Я пошел гулять!', u'Я :гл(дст,fff,мр,ед) :инф(дст)!'),
            (u'Я пошел!', u'Я :гл(дст,прш,мр,ед) :инф(дст)!'),
            (u'что такое?', u'* *'),
            ):
            print phrase, '|', template
            self.assert_(not matcher.phrase_match(phrase, template))

    def test_info_matching(self):
        for infos in (
            ('1,2,3', '1,2,3'),
            ('1,2,3', ''),
            ('1,2,3', ',2,'),
            ('1,2,3', '1,,3'),
            ('1,2,3', '1'),
            ):
            print infos
            self.assert_(matcher.info_match(*infos))
        for infos in (
            ('1,2', '1,2,3'),
            ('1,2,3', '1,3'),
            ('1,3,2', '1,3,,2')):
            print infos
            self.assert_(not matcher.info_match(*infos))
        
    def test_info_bindings(self):
        for info1, info2, bindings, new_bindings in (
            ('1,2,3', '1,?x,3', None, [{'?x': '2'}]),
            ('1,2,3', '?x,?x,3', None, False),
            ('1,2,3', '?y,?x,3', None, [{'?x': '2', '?y': '1'}]),
            ('1,2,3', '?y,?x,3', [{'?x': '1'}, {'?x': '2'}], [{'?x': '2', '?y': '1'}]),
            ('1,2,3', '?y,?x,3', [{'?x': '1'}, {'?x': '3'}], False),
            ('1,2,3', '?y,?x,3', [{'?x': '2', '?y': '1'}, {'?x': '2', '?y': '2'}],
             [{'?x': '2', '?y': '1'}]),
            ('1,2,3', '?y,2,3', [{'?x': '2'}, {'?x': '1'}],
             [{'?x': '2', '?y': '1'}, {'?x': '1', '?y': '1'}]),
            ('1,2,3', '?y,?x,3', [{'?x': '1'}], False),
            ):
            self.assertEqual(norm(matcher.info_match(info1, info2, bindings)),
                             norm(new_bindings))

    def test_word_bindings(self):
        for word, template, bindings in (
            (u'слово', u':сущ(?род,?число,?падеж)',
             [{u'?род': u'ср', u'?число': u'ед', u'?падеж': u'им'},
              {u'?род': u'ср', u'?число': u'ед', u'?падеж': u'вн'},]),
            ):
            self.assertEqual(norm(matcher.word_match(word, template)),
                             norm(bindings))

    def test_phrase_bindings(self):
        for phrase, template, bindings in (
            (u'Я пошел гулять побежал!',
             u'Я :гл(?x,прш,мр,?y) :инф(?x) :гл(?x,прш,мр,?y)!',
             {u'гл1': u'пошел', u'гл2': u'побежал', u'инф1': u'гулять'}),
            (u'Кто-то взял ключ',
             u':мест(?род,?число,?пад) :гл(дст,прш,?род,?число) :сущ(?род,?число,?пад)',
             {u'мест': u'кто-то', u'гл': u'взял', u'сущ': u'ключ'}),
            (u'Кто-то взял ключ',
             u':мест(?род,?число,?падеж) :гл :сущ(?род,?число,?падеж)', {}),
            (u'Кто-то взял ключ',
             u':мест(?род,?число,) :гл(дст,,?род,?число) :сущ(?род,?число,?падеж)', {}),
            ):
            print phrase, '|', template
            match = matcher.phrase_match(phrase, template)
            self.assert_(match)
            if bindings:
                for k, v in bindings.iteritems():
                    self.assertEqual(v, match.get(k))
        for phrase, template in (
            (u'Я пойду гулять!', u'Я :гл(дст,?x,мр,ед) :инф(?x)'),
            ):
            print phrase, '|', template
            self.assert_(not matcher.phrase_match(phrase, template))


def norm(x):
    if type(x) in (tuple, list): return list(sorted(x))
    return x


if __name__ == '__main__':
    unittest.main()
