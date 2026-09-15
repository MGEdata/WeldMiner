import json
import re
import os
import pandas as pd
from lxml import etree
import openpyxl

class ElsevierXmlReader(object):
    """Parsing Elsevier articles."""

    def __init__(self, path):
        self.path = path
        self.xml = etree.parse(self.path, etree.XMLParser())

        ns = {"bk": "http://www.elsevier.com/xml/bk/dtd",
              "cals": "http://www.elsevier.com/xml/common/cals/dtd",
              "ce": "http://www.elsevier.com/xml/common/dtd",
              "ja": "http://www.elsevier.com/xml/ja/dtd",
              "mml": "http://www.w3.org/1998/Math/MathML",
              "sa": "http://www.elsevier.com/xml/common/struct-aff/dtd",
              "sb": "http://www.elsevier.com/xml/common/struct-bib/dtd",
              "tb": "http://www.elsevier.com/xml/common/table/dtd",
              "xlink": "http://www.w3.org/1999/xlink",
              "xocs": "http://www.elsevier.com/xml/xocs/dtd",
              "dc": "http://purl.org/dc/elements/1.1/",
              "dcterms": "http://purl.org/dc/terms/",
              "prism": "http://prismstandard.org/namespaces/basic/2.0/",
              "xsi": "http://www.w3.org/2001/XMLSchema-instance"}

        try:
            self.doi = self.xml.xpath('//prism:doi/text()', namespaces=ns)[0]
        except:
            print(self.path, ' is error')

        try:
            self.eid = self.xml.xpath('//xocs:eid/text()', namespaces=ns)[0]
        except:
            self.eid = self.xml.xpath('//prism:doi', namespaces=ns)[0].getprevious().text
        self.title = self.xml.xpath('//dc:title/text()', namespaces=ns)[0].strip()
        self.date = self.xml.xpath('//prism:coverDate/text()', namespaces=ns)[0]
        self.journal = self.xml.xpath('//prism:publicationName/text()', namespaces=ns)[0]


        # getabstract
        abs = self.xml.xpath('//dc:description', namespaces=ns)
        pattern = re.compile(r'<[^>]+>', re.S)
        temp = etree.tostring(abs[0], encoding='utf-8').decode('utf-8')
        text = temp.replace("\n", "")
        text = re.sub(r"\s{2,}", " ", text)
        text = pattern.sub('', text).strip('\n ')
        self.abstract = text[0:text.find('\n')]

        # getkeyword
        words = self.xml.xpath('//dcterms:subject', namespaces=ns)
        keywords_key = []
        keywords_value = []
        n = 1
        for word in words:
            keywords_value.append(word.text)
            keywords_key.append('keyword' + str(n))
            n += 1
        keywords = dict(zip(keywords_key, keywords_value))

        self.keywords = keywords

        # get content V2

        paras = self.xml.xpath('//ja:article/ja:body//ce:para', namespaces=ns)
        paras3 = self.xml.xpath('//ja:body//ce:section//ce:para', namespaces=ns)
        paras2 = self.xml.xpath('//xocs:rawtext/text()', namespaces=ns)
        full_text = []
        if paras:
            pattern = re.compile(r'<[^>]+>', re.S)
            para_obj = []
            h_li = ['', '', '']
            for para in paras:
                # Get the text content
                temp = etree.tostring(para, encoding='utf-8').decode('utf-8')
                para_text = pattern.sub('', temp)  # filter tags
                para_text = re.sub(r'\s{2,}', ' ', para_text).strip()

                if not para_text:
                    continue

                # Try to get hierarchy information
                parent = para.getparent()
                hierarchy = []

                # Walk up the tree to build hierarchy
                while parent is not None:
                    if parent.tag.endswith('section') or parent.tag.endswith('section-title'):
                        label = parent.find('ce:label', namespaces=ns)
                        title = parent.find('ce:section-title', namespaces=ns)
                        if label is not None and title is not None:
                            hierarchy.insert(0, f"{label.text} {title.text}")
                    parent = parent.getparent()
                if hierarchy:
                    para_dict = {
                        "tag": hierarchy[0],
                        "text": para_text
                    }
                else:
                    para_dict = {
                        "tag": [],
                        "text": para_text
                    }
                para_obj.append(para_dict)

                para_obj.append(para_dict)

                # full_text += self.abstract
                # full_text += "\n"
                full_text.append(para_dict)
        elif paras2:
            para_dict = {
                "tag": [],
                "text": paras2[0]
            }
            full_text.append(para_dict)
        elif paras3:
            pattern = re.compile(r'<[^>]+>', re.S)
            para_obj = []
            h_li = ['', '', '']
            for para in paras3:
                # Get the text content
                temp = etree.tostring(para, encoding='utf-8').decode('utf-8')
                para_text = pattern.sub('', temp)  # filter tags
                para_text = re.sub(r'\s{2,}', ' ', para_text).strip()

                if not para_text:
                    continue

                # Try to get hierarchy information
                parent = para.getparent()
                hierarchy = []

                # Walk up the tree to build hierarchy
                while parent is not None:
                    if parent.tag.endswith('section') or parent.tag.endswith('section-title'):
                        label = parent.find('ce:label', namespaces=ns)
                        title = parent.find('ce:section-title', namespaces=ns)
                        if label is not None and title is not None:
                            hierarchy.insert(0, f"{label.text} {title.text}")
                    parent = parent.getparent()
                if hierarchy:
                    para_dict = {
                        "tag": hierarchy[0],
                        "text": para_text
                    }
                else:
                    para_dict = {
                        "tag": [],
                        "text": para_text
                    }
                para_obj.append(para_dict)

                para_obj.append(para_dict)

                # full_text += self.abstract
                # full_text += "\n"
                full_text.append(para_dict)
        self.content = full_text
        # add figures
        figs = self.xml.xpath('//ce:floats/ce:figure', namespaces=ns)
        fig_obj = []

        for idx, fig in enumerate(figs):
            fig_xml = etree.tostring(fig, encoding='utf-8').decode('utf-8')
            fig_xml = re.sub(r'<ce:label[^S]+</ce:label>', '', fig_xml)  # delete <ce:label> content
            fig_caption = self.filter(fig_xml)
            fig_label = ""
            try:
                fig_label = fig.find('ce:label', namespaces=ns).text + '. '
            except:
                pass
            fig_high_res = "https://ars.els-cdn.com/content/image/" + self.eid + "-gr" + str(idx + 1) + "_lrg.jpg"
            fig_full_size = "https://ars.els-cdn.com/content/image/" + self.eid + "-gr" + str(idx + 1) + ".jpg"

            fig_dict = {"label": fig_label,
                        "caption": fig_caption,
                        "high-res": fig_high_res,
                        "full-size": fig_full_size}

            fig_obj.append(fig_dict)

        self.figure = fig_obj

        # add refs
        refs = self.xml.xpath('//ce:bib-reference', namespaces=ns)
        ref_obj = []

        for n, ref in enumerate(refs):

            d = {}
            title_li = ['', '']
            ref_key = ['label', 'textref', 'author', 'title', 'publication', 'publisher', 'date', 'volume',
                       'issue', 'first_page', 'last_page', 'edition', 'comment', 'location']
            ref_value = ['' for i in range(len(ref_key))]
            ref_dic = dict(zip(ref_key, ref_value))

            for element in refs[n].iter():
                if isinstance(element.text, str) and len(re.findall(r'\S', element.text)) > 0:
                    # print("%s - %s" % (element.tag, element.text))
                    if re.sub(r'\{.*\}', '', element.tag) == 'maintitle':
                        # print(element.text)
                        if re.sub(r'\{.*\}', '', element.getparent().getparent().tag) == 'contribution':
                            title_li[0] = element.text
                        else:
                            title_li[1] = element.text
                    else:
                        new_key = re.sub(r'\{.*\}', '', element.tag)
                        new_value = element.text
                        d[new_key] = new_value

            # get ref label
            ref_dic['label'] = refs[n].find('ce:label', namespaces=ns).text
            # get textref
            if d.get('textref'):
                ref_dic['textref'] = d['textref']
                ref_obj.append(ref_dic)
                continue
                # print('succeed')
            # get ref author
            temp = etree.tostring(refs[n], encoding='utf-8').decode('utf-8')
            auts = re.findall(r'<ce:given-name>(.*?)</ce:given-name>|<ce:surname>(.*?)</ce:surname>', temp)
            author_value = []
            author_key = []
            for n in range(0, len(auts), 2):
                if len(auts) % 2 == 1:
                    author_value.append(auts[n][1])
                else:
                    author_value.append(auts[n][0] + ' ' + auts[n + 1][1])
                author_key.append('author' + str(int(n / 2) + 1))
                # author_value.append(auts[n][0] + ' ' +  auts[n+1][1])
                # author_key.append('author' + str(int(n/2) + 1))
            ref_dic['author'] = dict(zip(author_key, author_value))

            # get ref other info
            ref_dic['title'] = title_li[0]
            ref_dic['publication'] = title_li[1]
            ref_dic['publisher'] = d.get('name', '')
            ref_dic['date'] = d.get('date', '')
            ref_dic['volume'] = d.get('volume-nr', '')
            ref_dic['issue'] = d.get('issue-nr', '')
            ref_dic['first_page'] = d.get('first-page', '')
            ref_dic['last_page'] = d.get('last-page', '')
            ref_dic['edition'] = d.get('edition', '')
            ref_dic['comment'] = d.get('comment', '')
            ref_dic['location'] = d.get('location', '')

            ref_obj.append(ref_dic)

        self.refs = ref_obj

    def filter(self, string):
        """filter some tags in str"""

        string = re.sub(r'<[^>]+>', '', string, re.S)  # filter tags
        string = re.sub(r'\s{2,}', ' ', string)  # merge text
        string = string.strip()

        return string

    def dic(self):
        """Converting article infomation to dict type."""

        attrib = {"doi": self.doi,
                  "title": self.title,
                  "journal": self.journal,
                  "abstract": self.abstract,
                  "content": self.content,
                  "figure": self.figure,
                  }
        return attrib

def from_json_to_excel(input_file,output_path):
    xls = openpyxl.Workbook()
    sht = xls.create_sheet("parags", index=0)
    # sht.cell(col_i, 1, line)  # 写入表格的只能是字符型数据
    # xls.save(r'C:\Users\win\Desktop\xml_get\data.xlsx')
    col_i = 1
    with open(input_file,"r",encoding="utf8") as file:
        parag_info = json.load(file)
    for info in parag_info:
        doi = info["doi"]
        parags = info["content"]
        for p_info in parags:
            section_name = p_info["h1"]
            text = p_info["text"]
            sht.cell(col_i, 1, doi)
            sht.cell(col_i, 2, section_name)
            sht.cell(col_i, 3, text)
            col_i += 1
    xls.save(output_path)

def file_to_caption(file):
    fig_caps = dict()
    for article in file:
        figs_ = list()
        for type,info in article.items():

            if type == "doi":
                article_doi = info
            if type == "figure":
                for fig in info:
                    if "caption" in fig.keys():
                        fig_info = dict()
                        caption = fig['caption']
                        label = fig['label']
                        caption = re.sub(r"<[^<>]+>", "", caption)
                        caption = re.sub(r"\s+", " ", caption)
                        if caption:
                            # if "creep curve" in caption:
                                fig_info['label'] = label
                                fig_info['caption'] = caption
                                fig_info['high-res'] = fig["high-res"]
                                figs_.append(fig_info)
        if figs_:
            fig_caps[article_doi] = figs_
    return fig_caps

# if __name__ == '__main__':
#     fig_url = []
#     xml_path = r'E:\项目\管线钢知识图谱\氢脆相关数据抽取\钢铁氢脆xml_html\xml'
#     dir_list = os.listdir(xml_path)
#     # file = []
#     # error = []
#     for idx, f in enumerate(dir_list):
#         try:
#             path = os.path.join(xml_path,f)
#             temp = ElsevierXmlReader(path).dic()
#             doi = temp["doi"]
#             doi_ = doi.replace("/","-",1)
#             path_ = os.path.join(xml_path,doi_+".xml")
#             os.rename(path, path_)
#
#         except Exception as e:
#             print(e)
#     # with open(r"E:\项目\材料全要素数据采集和积累\知网\抽取示例\10.1016-0029-5493(95)01138-2.json",'w',encoding="utf8") as file:
#     #     file.write(json.dumps(temp, indent=2))



from .table_extractor import TableExtractorToAlloy

def get_full_text(doi):
    """
    Function to extract full text of an article with doi.
    :param doi: Required parameter, of type string, representing the doi of article. \
    For example, "10.1016/j.jallcom.2016.07.159".
    :return: The full text of the article.
    The return type is a JSON-formatted object after parsing, represented as a string, containing information including the doi, title, journal, abstract, content, figure, and table information.
    """
    file_path = "test_file"
    f_doi = doi.replace("/", "-",1)
    full_text = ElsevierXmlReader(os.path.join(file_path,f_doi+".xml")).dic()

    table_extractor_m = TableExtractorToAlloy(os.path.join(file_path, f_doi + ".xml"))
    tables = "Failed to extract tables"
    try:
        tables = table_extractor_m.get_xml_tables(doi)
    except Exception as e:
        print(e)
    full_text["tables"] = tables

    return full_text

