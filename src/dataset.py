""" reads a corpus """

from collections import Counter

import csv
from story import Story

class RocDataset:

    """ a class to help us use ROCStory data for machine learning """

    def __init__(self):

        # self.train_path = '/home/william.hancock/workspace/data/lsdsem/ukp/train_rocstories_kde.csv'
        self.dev_path = '/home/william.hancock/workspace/data/lsdsem/compiled/dev_storycloze.csv'
        self.test_path = '/home/william.hancock/workspace/data/lsdsem/compiled/test_storycloze.csv'

        self.load_data()


    def load_data(self):

        # train_data = self.parse_csv(self.train_path)
        dev_data = self.parse_csv(self.dev_path)
        test_data = self.parse_csv(self.test_path)
        

        print("ORIG TRAIN SIZE", len(dev_data))
        print("ORIG DEV SIZE", len(test_data))


        dev_pivot = int(len(dev_data) * .85)
        dev_for_train = dev_data[:dev_pivot]
        dev_for_dev = dev_data[dev_pivot:]



        # take a subset of train
        # train_pivot = int(len(train_data) * .05)
        self.train_data = dev_for_train

        # dev_pivot = int(len(dev_data) * .1)
        self.dev_data = dev_for_dev # [:dev_pivot]

        self.test_data = test_data


        print("TRAIN SIZE:", len(self.train_data))
        print("DEV SIZE:", len(self.dev_data))


        # build a tensor that maps words in our data to indices
        self.corpus = self.train_data + self.dev_data + self.test_data
        self.corpus_freq = self.build_freq_dict()




    def count(self):
        """ return size of corpus """
        return len(self.corpus_freq.keys())


    def get_good_bad_split(self, embedding, story_list):
        """
        take each story and generate two training examples from it:

        story_body      ending_one      ending_one_features     ending_one_label
        story_body      ending_two      ending_two_features     ending_two_label
        ...
        """

        examples = []

        for story in story_list:

            context_embedded = embedding.embed(story.get_context_tokens(), 80)

            for (idx, ending_tokens) in enumerate(story.get_tokenized_endings()):

                ending_embedded = embedding.embed(ending_tokens, 20)
                label = [1,0] if story.ending_idx==idx else [0,1]

                examples.append((context_embedded, ending_embedded, [None], label))


        return examples



    def get_dev_repr(self, embedding, story_list):

        """
        generate one example from each story

        story_body  ending_one  ending_one_feats    ending_two  ending_two_feats    correct_label
        ...

        """

        examples = []

        for story in story_list:

            ending_one = story.get_tokenized_endings()[0]
            ending_two = story.get_tokenized_endings()[1]

            context_embedded = embedding.embed(story.get_context_tokens(), 80)
            ending_one_embedded = embedding.embed(ending_one, 20)
            ending_two_embedded = embedding.embed(ending_two, 20)

            label = [1,0] if story.ending_idx==0 else [0,1]

            examples.append((
                context_embedded, 
                ending_one_embedded, 
                story.get_end_one_feats(), 
                ending_two_embedded, 
                story.get_end_two_feats(),
                story.get_shared_feats(),
                label
                ))

        return examples





    def get_vocab(self):
        return self.corpus_freq.keys()


    def build_freq_dict(self):
        """ 
            purely a cosmetic thing: build a token counter to assign IDs to
            tokens in an ordinal manner
        """

        tokens = Counter()

        for story in self.corpus:
            tokens.update(story.get_freq())

        return tokens




    def parse_csv(self, path):
        """ parse the csv files """

        stories = []

        with open(path, 'r') as csvfile:

            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            header = next(reader)

            for row in reader:

                story_id = row[0]
                sentences = []
                for text in row[1:5]:
                    sentences.append(text)
                potential_endings = []
                for text in row[5:7]:
                    potential_endings.append(text)

                correct_ending_idx = int(row[7]) - 1

                end_one_feats = []
                end_two_feats = []
                shared_feats = []

                if len(row) > 8:
                    for idx in range(8, len(header)):
                        if 'e1' in header[idx]:
                            end_one_feats.append(float(row[idx]))
                        elif 'e2' in header[idx]:
                            end_two_feats.append(float(row[idx]))
                        else:
                            shared_feats.append(float(row[idx]))

                end_feats = (end_one_feats, end_two_feats)

                stories.append(
                    Story(
                        story_id, 
                        sentences, 
                        potential_endings, 
                        end_feats,
                        shared_feats,
                        correct_ending_idx
                        ))


        return stories
