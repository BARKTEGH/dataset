import json

import stanfordcorenlp as stanfordcorenlp


class Feature(object):

    def __init__(self):
        self.nlp = stanfordcorenlp.StanfordCoreNLP('http://localhost', port=9000)
        self.props = {'annotators': 'tokenize, ssplit, ner, parse, depparse, coref', 'pipelineLanguage': 'en', 'outputFormat': 'json'}
        self.feature = ["word", "pos","ner", "depparse"]

    def close(self):
        self.nlp.close()

    def get_res_from_server(self, sentence):
        res = self.nlp.annotate(sentence, properties=self.props)
        return json.loads(res)

    def get_feture(self, res):
        res_dict = {}
        sentence = res["sentences"][0]
        tokens = sentence["tokens"]
        word_list = []
        pos_list = []
        ner_list = []
        index_list = []

        for token in tokens:
            word_list.append(token["word"])
            pos_list.append(token["pos"])
            ner_list.append(token["ner"])
            index_list.append(token["index"])

        res_dict["token"] = word_list
        if "pos" in self.feature:
            res_dict["stanford_pos"] = pos_list
        if "ner" in self.feature:
            res_dict["stanford_ner"] = ner_list
        if "parse" in self.feature:
            res_dict["parse"] = sentence["parse"]
        if "depparse" in self.feature:
            # 需要注意从1开始 0为ROOT
            # 会出现一个单词依赖两个单词，出现覆盖现象，导致无root出现
            deps = sentence["enhancedDependencies"]

            head_dependent = [-1] * len(tokens)
            deprel = [-1] * len(tokens)
            for dep in deps:
                governor = dep["governor"]
                dependent = dep["dependent"]
                deprel[dependent-1] = dep["dep"]
                if head_dependent[dependent-1] != -1:
                    if governor == 0:
                        head_dependent[dependent-1] = governor
                else:
                    head_dependent[dependent - 1] = governor
            for i, index in enumerate(head_dependent):
                 if head_dependent[i] == -1:
                     head_dependent[i] = i
            assert not all(head_dependent)
            res_dict["stanford_head"] = head_dependent
            res_dict["stanford_deprel"] = deprel
        return res_dict

    def get_entity_position(self, entity1, entity2, words):
        entity1__list = entity1.split()
        entity2__list = entity2.split()
        entity1_before = 0
        entity1_back = 0
        entity2_before = 1
        entity2_back = 1

        for i, word in enumerate(words):
            if entity1__list[0] == word:
                index = 1
                while index < len(entity1__list) and (index+i) < len(words):
                    if words[i+index] == entity1__list[index]:
                        index += 1
                    else:
                        break
                if index == len(entity1__list):
                    entity1_before = i
                    entity1_back = i+index-1
            if entity2__list[0] == word:
                index = 1
                while index < len(entity2__list) and (index + i) < len(words):
                    if words[i + index] == entity2__list[index]:
                        index += 1
                    else:
                        break
                if index == len(entity2__list):
                    entity2_before = i
                    entity2_back = i + index - 1

        return entity1_before, entity1_back, entity2_before, entity2_back

    def parse_sentence(self, sent):
        entity1 = sent["suj_text"]
        entity2 = sent["obj_text"]
        sentence = sent["sentText"]
        res = self.get_res_from_server(sentence)
        feature = self.get_feture(res)
        # 添加两个实体的位置
        entity1_before, entity1_back, entity2_before, entity2_back = \
            self.get_entity_position(entity1, entity2, feature["token"])
        feature["subj_text"] = entity1
        feature["subj_start"] = entity1_before
        feature["subj_end"] = entity1_back
        feature["obj_text"] = entity2
        feature["obj_start"] = entity2_before
        feature["obj_end"] = entity2_back
        feature["subj_type"] = feature["stanford_ner"][entity1_before]
        feature["obj_type"] = feature["stanford_ner"][entity2_before]
        feature["relation"] = sent["label"]
        sent.pop("suj_text")
        sent.pop("obj_text")
        sent.pop("label")
        feature.update(sent)
        return feature

    def save(self, old_file, new_file):
        data = json.load(open(old_file, 'r'))
        res = []
        count = 0
        for i, a in enumerate(data):
            res.append(self.parse_sentence(a))
            if (i+1)%1000 == 0:
                print("已处理到第{}行数据".format(i+1))
        json.dump(res,open(new_file, "w"))


if __name__ == "__main__":
    data = {
        "sentText": "But Mr. Clinton did take a swipe at Karl Rove , the senior adviser to President Bush , for his reported association with the disgraced lobbyist Jack Abramoff .",
        "suj_text": "Karl", "obj_text": "Jack", "label": "None"}
    feature = Feature()
    # feature.save("../data/new/all.json", "../data/all.json")
    print(feature.parse_sentence(data))
