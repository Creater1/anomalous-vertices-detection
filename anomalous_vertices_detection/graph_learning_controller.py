import os
import time

from graphlab import SFrame, extensions
from pandas import DataFrame

from GraphML.learners.gllearner import GlLearner
from GraphML.samplers.graph_sampler import GraphSampler
from configs.config import *
from feature_controller import FeatureController
from graphs.graph_factory import GraphFactory
from ml_controller import MlController
from utils import utils


class GraphLearningController:
    def __init__(self, cls, labels, config):
        """ Initialize a class the combines ml and graphs.

        Parameters
        ----------
        cls : AbstractLearner
            An object of a class the implements AbstractLearner
        labels : dict
            Map of binary labels for instance: {"neg": "Negative", "pos": "Positive"}
        config : GraphConfig
            config object that contains all the necessary information about the graph
        """
        self._labels = labels
        self._ml = MlController(cls.set_randomforest_classifier())
        self._config = config

    @staticmethod
    def extract_features_for_set(graph, dataset, output_path, max_items_num):
        """ Extracts features for given set and writes it to file.

            Parameters
            ----------
            graph : AbstractGraph

            dataset : list, iterable
               List that contains the name of the objects(vertex/edge) that
               their features should be extracted.

            output_path : string
               Path including file name for writing the extracted features.

        """
        features = FeatureController(graph)
        print "Graph loaded"
        features.extract_features(dataset, max_items_num=max_items_num)
        os.rename(temp_path, output_path)
        print "Features were written to: " + output_path

    def create_training_test_sets(self, my_graph, test_path, train_path, test_size, training_size,
                                  labels_path=None):
        """
        Creates and extracts features for training and test set.

        Parameters
        ----------
        my_graph : AbstractGraph
            A graph object that implements the AbstractGraph interface
        test_path : string
            A path to where the test set should be saved
        train_path : string
            A path to where the training set should be saved
        test_size : int
            The size of the test set that should be generated
        training_size : int
            The size of the training set that should be generated
        labels_path : string, (default=None)
            The path to where the labels should be saved.
        """
        if not (utils.is_valid_path(train_path) and utils.is_valid_path(test_path)):
            gs = GraphSampler(my_graph, self._config.vertex_min_edge_number, self._config.vertex_max_edge_number)
            if labels_path:
                my_graph.write_nodes_labels(labels_path)
            training_set, test_set = gs.split_training_test_set(training_size, test_size)

            self.extract_features_for_set(my_graph, test_set, test_path, test_size["neg"] + test_size["pos"])
            self.extract_features_for_set(my_graph, training_set, train_path,
                                          training_size["neg"] + training_size["pos"])
        else:
            print "Existing files were loaded."

    def classify_data(self, my_graph, test_path, train_path, test_size,
                      training_size, id_col_name="src", labels_path=None):
        """Execute the link classifier

        Parameters
        ----------
        my_graph : AbstractGraph
            A graph object that implements the AbstractGraph interface
        test_path : string
            A path to where the test set should be saved
        train_path : string
            A path to where the training set should be saved
        test_size : int
            The size of the test set that should be generated
        training_size : int
            The size of the training set that should be generated
        id_col_name : string
            The column name of the vertices id
        labels_path : string, (default=None)
            The path to where the labels should be saved.
        """
        print "Setting training and test sets"
        if my_graph.is_directed:
            meta_data_cols = ["dst", "src", "out_degree_v", "in_degree_v", "out_degree_u", "in_degree_u"]
            # meta_data_cols = ["dst", "src"]
        else:
            meta_data_cols = ["dst", "src", "number_of_friends_u", "number_of_friends_v"]

        # meta_data_cols = ["dst"]
        self.create_training_test_sets(my_graph, test_path, train_path, test_size=test_size,
                                       training_size=training_size, is_labeled=my_graph.has_labels,
                                       labels_path=labels_path)  # Training the classifier
        self._ml.load_training_set(train_path, "edge_label", id_col_name, meta_data_cols)
        print("Training 10-fold validation: {}".format(self._ml.k_fold_validation()))
        self._ml.load_test_set(test_path, "edge_label", id_col_name, meta_data_cols)
        self._ml.train_classifier()
        # Testing the classifier
        print("Test evaluation: {}".format(self._ml.evaluate_test()))

    def classify_by_links(self, my_graph, test_path, train_path, results_output_path, real_labels_path, test_size,
                          train_size):
        """Execute the vertex anomaly detection process

        Parameters
        ----------
        my_graph : AbstractGraph
            A graph object that implements the AbstractGraph interface
        test_path : string
            A path to where the test set should be saved
        training_size : int
            The size of the training set that should be generated
        results_output_path : string
            The path to where the classification results should be saved
        real_labels_path : string
            The path to which the labels should be saved
        train_path : string
            A path to where the training set should be saved
        test_size : int
            The size of the test set that should be generated
        """
        self.classify_data(my_graph, test_path, train_path, test_size, train_size, labels_path=real_labels_path)
        classified = self._ml.classify_by_links_probability()
        # Output
        classified = self._ml._learner.merge_with_labels(classified, real_labels_path)
        if isinstance(classified, SFrame):
            print "________________________________"
            print results_output_path
            print "________________________________"
            classified.save(results_output_path)
        if isinstance(classified, DataFrame):
            classified.to_csv(results_output_path)
        try:
            print self._ml.validate_prediction_by_links(classified)
        except extensions._ToolkitError:
            print "One class"


def get_output_paths(set_name, argv):
    test_path, training_path, result_path, labels_output_path = io_path + set_name + "_test.csv", \
                                                                io_path + set_name + "_train.csv", \
                                                                results_path + set_name + "_res.csv", \
                                                                io_path + set_name + "_labels.csv"
    if len(argv) != 2:
        new_train_test = utils.to_create_new_file("train and test")
    else:
        new_train_test, load_new_graph = [x == "True" for x in argv]
    if new_train_test:
        training_path = utils.generate_file_name(training_path)
        test_path = utils.generate_file_name(test_path)
    else:
        training_path = utils.get_newest_files(io_path, set_name + "_train")
        print("Loading " + training_path)
        test_path = utils.get_newest_files(io_path, set_name + "_test")
        print("Loading " + test_path)
    if len(argv) != 2:
        if new_train_test:
            load_new_graph = utils.to_create_new_file("graph", "To load new ")
        else:
            load_new_graph = False
    return load_new_graph, new_train_test, result_path, test_path, training_path, labels_output_path


def main(argv, graph_config=None, my_graph=None):
    print "start"
    # labels = ["Real", "Fake"]
    # argv = ["True", "False", "True"]
    labels = {"neg": "Real", "pos": "Fake"}
    max_num_of_edges = 7000000
    gf = GraphFactory()
    # cls = SkLearner(labels=labels)
    cls = GlLearner(labels=labels)
    dataset_config = academia_config
    if graph_config:
        dataset_config = graph_config
    gl = GraphLearningController(cls, labels, dataset_config)
    load_new_graph, new_test, result_path, test_path, training_path, labels_output_path = \
        get_output_paths(dataset_config.name, argv)
    result_path = utils.generate_file_name(result_path)
    if not new_test:
        max_num_of_edges = 2
    if not my_graph:
        if load_new_graph:
            if dataset_config.type == "ba":
                my_graph = gf.make_ba_graph_with_fake_profiles(dataset_config.node_number, dataset_config.edge_number,
                                                               fake_users_number=int(0.1*dataset_config.node_number),
                                                               max_neighbors=dataset_config.max_neighbors_number,
                                                               pos_label=labels["pos"], neg_label=labels["neg"])
            if dataset_config.type == "regular":
                my_graph = gf.make_graph(dataset_config.data_path, labels_path=dataset_config.labels_path,
                                         is_directed=dataset_config.is_directed, pos_label=labels["pos"],
                                         neg_label=labels["neg"], start_line=dataset_config._first_line,
                                         max_num_of_edges=max_num_of_edges,  # blacklist_path=wiki_blacklist,
                                         delimiter=dataset_config.delimiter, package="Networkx", weight_field="weight")
            if dataset_config.type == "simulation":
                my_graph = gf.make_graph_with_fake_profiles(dataset_config.data_path,
                                                            edge_number=dataset_config.max_neighbors_number,
                                                            labels_path=dataset_config.labels_path,
                                                            is_directed=dataset_config.is_directed,
                                                            pos_label=labels["pos"],
                                                            neg_label=labels["neg"],
                                                            start_line=dataset_config._first_line,
                                                            max_num_of_edges=max_num_of_edges,
                                                            delimiter=dataset_config.delimiter, package="Networkx",
                                                            weight_field="weight")
            if max_num_of_edges > 2:
                # my_graph.save_graph(dataset_config.name, "sgraph")
                my_graph.save_graph(dataset_config.name, "pickle")

                # my_graph.save_graph(dataset_config.name, "graphml")
        else:
            my_graph = gf.load_graph(is_directed=dataset_config.is_directed, pos_label=labels["pos"],
                                     neg_label=labels["neg"], labels_path=labels_output_path,
                                     graph_name=dataset_config.name)  # , weight_field="weight")

    gl.classify_by_links(my_graph, test_path, training_path, result_path,
                         labels_output_path, test_size={"neg": 20, "pos": 20},
                         train_size={"neg": 20, "pos": 20})
    print gl._ml.validation_classification_by_links("twitter_labels.csv")
    print "end"
    return my_graph
