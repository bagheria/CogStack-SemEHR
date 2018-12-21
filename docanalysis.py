import utils
from os.path import join, isfile, split
import logging
import study_analyzer


class BasicAnn(object):
    """
    a simple NLP (Named Entity) annotation class
    """
    def __init__(self, str, start, end):
        self._str = str
        self._start = start
        self._end = end
        self._id = -1

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def str(self):
        return self._str

    @str.setter
    def str(self, value):
        self._str = value

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        self._start = value

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value):
        self._end = value

    def overlap(self, other_ann):
        if other_ann.start <= self.start <= other_ann.end or other_ann.start <= self.end <= other_ann.end:
            return True
        else:
            return False

    def is_larger(self, other_ann):
        return self.start <= other_ann.start and self.end >= other_ann.end \
               and not (self.start == other_ann.start and self.end == other_ann.end)

    def serialise_json(self):
        return {'start': self.start, 'end': self.end, 'str': self.str, 'id': self.id}

class ContextedAnn(BasicAnn):
    """
    a contextulised annotation class (negation/tempolarity/experiencer)
    """
    def __init__(self, str, start, end, negation, temporality, experiencer):
        self._neg = negation
        self._temp = temporality
        self._exp = experiencer
        super(ContextedAnn, self).__init__(str, start, end)

    @property
    def negation(self):
        return self._neg

    @negation.setter
    def negation(self, value):
        self._neg = value

    @property
    def temporality(self):
        return self._temp

    @temporality.setter
    def temporality(self, value):
        self._temp = value

    @property
    def experiencer(self):
        return self._exp

    @experiencer.setter
    def experiencer(self, value):
        self._exp = value

    def serialise_json(self):
        dict = super(ContextedAnn, self).serialise_json()
        dict['negation'] = self.negation
        dict['temporality'] = self.temporality
        dict['experiencer'] = self.experiencer
        return dict


class PhenotypeAnn(ContextedAnn):
    """
    a simple customisable phenotype annotation (two attributes for customised attributes)
    """
    def __init__(self, str, start, end,
                 negation, temporality, experiencer,
                 major_type, minor_type):
        super(PhenotypeAnn, self).__init__(str, start, end, negation, temporality, experiencer)
        self._major_type = major_type
        self._minor_type = minor_type

    @property
    def major_type(self):
        return self._major_type

    @major_type.setter
    def major_type(self, value):
        self._major_type = value

    @property
    def minor_type(self):
        return self._minor_type

    @minor_type.setter
    def minor_type(self, value):
        self._minor_type = value

    def serialise_json(self):
        dict = super(PhenotypeAnn, self).serialise_json()
        dict['major_type'] = self.major_type
        dict['minor_type'] = self.minor_type
        return dict


class SemEHRAnn(ContextedAnn):
    """
    SemEHR Annotation Class
    """
    def __init__(self, str, start, end,
                 negation, temporality, experiencer,
                 cui, sty, pref, ann_type):
        super(SemEHRAnn, self).__init__(str, start, end, negation, temporality, experiencer)
        self._cui = cui
        self._sty = sty
        self._pref = pref
        self._ann_type = ann_type
        self._study_concepts = []
        self._ruled_by = []

    @property
    def cui(self):
        return self._cui

    @cui.setter
    def cui(self, value):
        self._cui = value

    @property
    def sty(self):
        return self._sty

    @sty.setter
    def sty(self, value):
        self._sty = value

    @property
    def ann_type(self):
        return self._ann_type

    @ann_type.setter
    def ann_type(self, value):
        self._ann_type = value

    @property
    def pref(self):
        return self._pref

    @pref.setter
    def pref(self, value):
        self._pref = value

    @property
    def study_concepts(self):
        return self._study_concepts

    def add_study_concept(self, value):
        if value not in self._study_concepts:
            self._study_concepts.append(value)

    @property
    def ruled_by(self):
        return self._ruled_by

    def add_ruled_by(self, rule_name):
        if rule_name not in self._ruled_by:
            self._ruled_by.append(rule_name)

    def serialise_json(self):
        dict = super(SemEHRAnn, self).serialise_json()
        dict['sty'] = self.sty
        dict['cui'] = self.cui
        dict['pref'] = self.pref
        dict['study_concepts'] = self.study_concepts
        dict['ruled_by'] = self.ruled_by
        return dict


class SemEHRAnnDoc(object):
    """
    SemEHR annotation Doc
    """
    def __init__(self, file_path, file_key=None):
        if file_key is None:
            p, fn = split(file_path)
            file_key = fn[:fn.index('.')]
        self._fk = file_key
        self._doc = utils.load_json_data(file_path)
        self._anns = []
        self._phenotype_anns = []
        self._sentences = []
        self._others = []
        self.load_anns()

    def load_anns(self):
        all_anns = self._anns
        panns = self._phenotype_anns
        for anns in self._doc['annotations']:
            for ann in anns:
                t = ann['type']
                if t == 'Mention':
                    a = SemEHRAnn(ann['features']['string_orig'],
                                  int(ann['startNode']['offset']),
                                  int(ann['endNode']['offset']),

                                  ann['features']['Negation'],
                                  ann['features']['Temporality'],
                                  ann['features']['Experiencer'],

                                  ann['features']['inst'],
                                  ann['features']['STY'],
                                  ann['features']['PREF'],
                                  t)
                    all_anns.append(a)
                    a.id = 'cui-%s' % len(all_anns)
                elif t == 'Phenotype':
                    a = PhenotypeAnn(ann['features']['string_orig'],
                                     int(ann['startNode']['offset']),
                                     int(ann['endNode']['offset']),

                                     ann['features']['Negation'],
                                     ann['features']['Temporality'],
                                     ann['features']['Experiencer'],

                                     ann['features']['majorType'],
                                     ann['features']['minorType'])
                    panns.append(a)
                    a.id = 'phe-%s' % len(panns)
                elif t == 'Sentence':
                    a = BasicAnn('Sentence',
                                 int(ann['startNode']['offset']),
                                 int(ann['endNode']['offset']))
                    self._sentences.append(a)
                    a.id = 'sent-%s' % len(self._sentences)
                else:
                    self._others.append(ann)

        sorted(all_anns, key=lambda x: x.start)

    @property
    def file_key(self):
        return self._fk

    def get_ann_sentence(self, ann):
        sent = None
        for s in self.sentences:
            if ann.overlap(s):
                sent = s
                break
        if sent is None:
            print 'sentence not found for %s' % ann.__dict__
            return None
        return sent

    @property
    def annotations(self):
        return self._anns

    @property
    def sentences(self):
        return self._sentences

    @property
    def phenotypes(self):
        return self._phenotype_anns

    def serialise_json(self):
        return {'annotations': [ann.serialise_json() for ann in self.annotations],
                'phenotypes': [ann.serialise_json() for ann in self.phenotypes],
                'sentences': [ann.serialise_json() for ann in self.sentences]}


class FulltextReader(object):

    def __init__(self, folder, pattern):
        self._folder = folder
        self._pattern = pattern

    def read_full_text(self, fk):
        p = join(self._folder, self._pattern % fk)
        if isfile(p):
            return utils.read_text_file_as_string(p)
        else:
            return None


def analyse_doc_anns(ann_doc_path, rule_executor, text_reader, output_folder, fn_pattern='se_ann_%s.json',
                     study_analyzer=None):
    ann_doc = SemEHRAnnDoc(file_path=ann_doc_path)
    text = text_reader.read_full_text(ann_doc.file_key)
    if text is None:
        logging.error('file [%s] full text not found' % ann_doc.file_key)
        return

    study_concepts = study_analyzer.study_concepts if study_analyzer is not None else None
    for ann in ann_doc.annotations:
        is_a_concept = False
        if study_concepts is not None:
            for sc in study_concepts:
                if ann.cui in sc.concept_closure:
                    ann.add_study_concept(sc.name)
                    is_a_concept = True
                    logging.debug('%s [%s, %s] is one %s' % (ann.str, ann.start, ann.end, sc.name))
        else:
            is_a_concept = True
        if is_a_concept:
            sent = ann_doc.get_ann_sentence(ann)
            if sent is not None:
                ruled = False
                context_text = text[sent.start:sent.end]
                s_before = context_text[:ann.start-sent.start]
                s_end = context_text[ann.end-sent.start:]
                if not ruled:
                    # string orign rules - not used now
                    ruled, case_instance = rule_executor.execute_original_string_rules(ann.str)
                    rule = 'original-string-rule'
                if not ruled:
                    # post processing rules
                    ruled, case_instance, rule = \
                        rule_executor.execute_context_text(text, s_before, s_end, ann.str)
                if ruled:
                    ann.add_ruled_by(rule)
                    logging.debug('%s [%s, %s] ruled by %s' % (ann.str, ann.start, ann.end, rule))
    utils.save_json_array(ann_doc.serialise_json(), join(output_folder, fn_pattern % ann_doc.file_key))
    return ann_doc.serialise_json()


def process_doc_anns(anns_folder, full_text_folder, rule_config_file, output_folder,
                     study_folder=None,
                     study_config='study.json', full_text_fn_ptn='%s.txt', fn_pattern='se_ann_%s.json'):
    """
    multiple threading process doc anns
    :param anns_folder:
    :param full_text_folder:
    :param rule_config_file:
    :param output_folder:
    :param study_folder:
    :param study_config:
    :param full_text_fn_ptn:
    :param fn_pattern:
    :return:
    """
    sa = None
    ruler = None
    text_reader = FulltextReader(full_text_folder, full_text_fn_ptn)
    if study_folder is not None and study_folder != '':
        r = utils.load_json_data(join(study_folder, study_config))

        ret = study_analyzer.load_study_settings(study_folder,
                                                 umls_instance=None,
                                                 rule_setting_file=r['rule_setting_file'],
                                                 concept_filter_file=None if 'concept_filter_file' not in r else r['concept_filter_file'],
                                                 do_disjoint_computing=True if 'do_disjoint' not in r else r['do_disjoint'],
                                                 export_study_concept_only=False if 'export_study_concept' not in r else r['export_study_concept']
                                                 )
        sa = ret['study_analyzer']
        ruler = ret['ruler']
    else:
        logging.info('no study configuration provided, applying rules to all annotations...')
        ruler = study_analyzer.load_ruler(rule_config_file)

    # for ff in [f for f in listdir(anns_folder) if isfile(join(anns_folder, f))]:
    #     analyse_doc_anns(join(anns_folder, ff), ruler, text_reader, output_folder, fn_pattern, sa)
    utils.multi_thread_process_files(dir_path=anns_folder,
                                     file_extension='json',
                                     num_threads=10,
                                     process_func=analyse_doc_anns,
                                     args=[ruler, text_reader, output_folder, fn_pattern, sa])
    logging.info('post processing of ann docs done')


if __name__ == "__main__":
    pass
