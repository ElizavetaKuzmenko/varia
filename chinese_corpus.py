# coding: utf-8

import re, os, lxml.html, time
from collections import OrderedDict


# put the path to your file directory here
DIR_PATH = '/home/lizaku/PycharmProjects/varia/chinese_texts'
# put the path to the dictionary here
DICT_PATH = '/home/lizaku/PycharmProjects/varia/cedict_ts.u8'
# smart transription split
re_transcr = re.compile('([^\]]*\])')
re_punct = re.compile('[《》“”！。？：  -‘、…ａ；\n 　’—（）0-9，－]')
re_clean1 = re.compile('(</w>)+')
re_clean2 = re.compile('<w><ana lex="\n[^\n]*\n')
re_link = re.compile('(?:see_|see_also_|variant_of_|same_as_)([^,]*)')


def load_dict(path): # todo: save the dictionary in json and do not load it every time
    """
    transforms the dictionary file into a computationally feasible format
    :param path: the path to the dictionary
    :return: dictionary in the form {new_tok: (old_tok, transcr, transl) ...}
    """
    print('load dict...', time.asctime())
    cedict = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or line == ' CC-CEDICT\n':
                continue
            old, new, transcr, transl = line.strip().split(' ', 3)
            m = re_transcr.search(transl)
            if m is not None:
                transcr += ' ' + m.group(1)
                transl = transl.replace(m.group(1), '')
                scr, sl = transcr.split(']', 1)
                transcr = scr + ']'
                transl = sl + transl
            if new not in cedict:
                cedict[new] = [(old, transcr, transl)]
            else:
                cedict[new].append((old, transcr, transl))
    return cedict


def load_corpus(path, cedict):
    """
    load and read all the files, transform them into the required form, write it down
    :param path: path to the dir with files, where the processed files will be put as well
    :param cedict: Chinese dictionary
    """
    for f in os.listdir(path):
        if f.endswith('ml') and '_processed' not in f:
            print(f)
            new_f = open(os.path.join(path, f.rsplit('.', 1)[0] + '_processed.xml'), 'w', encoding="utf-8")
            # here goes all the transformation
            sentences = make_xml(os.path.join(path, f), cedict)
            # write the transformed sentences one after another
            with open(os.path.join(path, f), 'r', encoding='utf-8') as orig:
                text = orig.read()
                para = text.split('</para>')
                print('replacing...', time.asctime())
                n = 0
                for p in para:
                    try:
                        zh = re.findall('<se lang="zh">([^<]*)<', p, flags=re.DOTALL)[0]
                        p = p.replace(zh, sentences[zh])
                        new_f.write(p + '</para>')
                    except IndexError:
                        print(p)
                        new_f.write('</body></html>')
                    #text = re_clean1.sub('</w>', text)
                    #text = re_clean2.sub('', text)
                    n += 1
            new_f.close()


def extract_sentences(fname):
    """
    extract all Chinese sentences
    :param fname: path to the file
    :return: list of all Chinese sentences
    """
    with open(fname, 'r') as f:
        html = f.read().replace('<?xml version="1.0" encoding="utf-8"?>', '')
    root = lxml.html.fromstring(html)
    sentences = root.xpath(u'//se[contains(@lang, "zh")]/text()')
    return sentences


def make_xml(fname, cedict):
    """
    transform the sentences into RNC XML
    :param fname: path to the file
    :param cedict: Chinese dictionary
    :return: wrapped sentences
    """
    print('make xml...', time.asctime())
    sentences = extract_sentences(fname)
    sent_dict = OrderedDict()
    for sent in range(len(sentences)):
        orig_sent = sentences[sent]
        transformed = ''
        # take a sentence and divide it into chunks
        punct = re_punct.findall(sentences[sent])
        fragments = [x for x in re_punct.split(sentences[sent]) if x != '']
        punct_i = 0
        for fragment in fragments:
            # delete all the punctuation (keep in the original sentence)
            while len(fragment) > 0:
                # if we still have smth in the fragment...
                chunk = fragment
                # find the shortest dictionary entry
                # todo: there was some dynamic algorithm for this
                while chunk not in cedict and chunk != '':
                    chunk = chunk[:-1]
                if chunk == '':
                    word_xml = '\n<w>' + fragment + '</w>'
                    transformed += word_xml.replace('=" ', '="')
                    if len(punct) != 0:
                        try:
                            transformed += punct[punct_i]
                            punct_i += 1
                        except:
                            print(fragment)
                    fragment = fragment[1:]
                    continue
                # now we have the dictionary entry, extract its features and wrap into tags
                word_xml = '\n<w>'
                for elem in cedict[chunk]:
                    transcr = elem[1][1:-1]
                    # preprocess the translation
                    transl = elem[2].replace('&', 'and').replace('("', '(«').replace('/"', '/«').replace(' "', ' «').replace('" ', '» ').replace('")', '»)').replace('",', '»,')\
                        .replace('"/', '»/').replace(' ', '_').replace('/', ', ').replace('_, ', '').strip().strip(',')
                    links = re_link.findall(transl)
                    if links != []:
                        for link in links:
                            try:
                                char = link.split('[')[0].split('|')[1]
                            except IndexError:
                                char = link.split('[')[0].split('|')[0]
                            if char in cedict:
                                transl_char = cedict[char][0]
                                transl_char = transl_char[2].replace('&', 'and').replace('("', '(«').replace('/"', '/«').replace(
                                    ' "', ' «').replace('" ', '» ').replace('")', '»)').replace('",', '»,') \
                                    .replace('"/', '»/').replace(' ', '_').replace('/', ', ').replace('_, ', '').strip().strip(',')
                                transl = transl.replace(link, transl_char)
                                transl = re.sub('see_|see_also_|variant_of_|same_as_', '', transl)
                    word_xml += '<ana lex="%s" transcr="%s" sem="%s"/>' % (chunk, transcr, transl)
                word_xml += chunk + '</w>'
                transformed += word_xml.replace('=" ', '="')
                fragment = fragment[len(chunk):]
            if len(punct) != 0 and transformed[-1] not in punct:
                try:
                    transformed += punct[punct_i]
                    punct_i += 1
                except IndexError:
                    print(fragment)
        sent_dict[orig_sent] = transformed
    return sent_dict

if __name__ == '__main__':
    cedict = load_dict(DICT_PATH)
    load_corpus(DIR_PATH, cedict)