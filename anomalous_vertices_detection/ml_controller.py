from anomalous_vertices_detection.utils.exceptions import ValueNotSet
from anomalous_vertices_detection.utils.dataset import DataSetFactory, DataSet


class MlController(object):
    def __init__(self, learner):
        self._learner = learner
        self._training = DataSet()
        self._test = DataSet()

    def load_training_set(self, features, labels=None, feature_id_col_name=None, metadata_col_names=[]):
        """Loads the training set extracted features.

        Parameters
        ----------
        features : string
            path to the csv file that contains the features.
        labels : string, (default=None)
            The name of the label field in the csv  file.
        feature_id_col_name : string, (default=None)
            The name of the id field in the csv  file.
        metadata_col_names :  list[string], (default=None)
            List contains the name of the fields that should not be loaded.
        """
        self._training = self._learner.convert_data_to_format(features, labels, feature_id_col_name, metadata_col_names)

    def load_test_set(self, features, labels=None, feature_id_col_name=None, metadata_col_names=[]):
        """Loads the test set extracted features.

        Parameters
        ----------
        features : string
            path to the csv file that contains the features.
        labels : string, (default=None)
            The name of the label field in the csv  file.
        feature_id_col_name : string, (default=None)
            The name of the id field in the csv  file.
        metadata_col_names :  list[string], (default=None)
            List contains the name of the fields that should not be loaded.
        """
        self._test = self._learner.convert_data_to_format(features, labels, feature_id_col_name, metadata_col_names)

    def evaluate_test(self):
        """Run evaluation function on the test set.
         If there is no test set ValueNotSet
         exception will be thrown.

        """
        if self._test:
            return self._learner.get_evaluation(self._test)
        else:
            raise ValueNotSet("Test set was not defined.")

    def train_classifier(self):
        """Train the classifier.
        """
        self._learner.train_classifier(self._training)

    def predict(self):
        """Return a binary classification on the test set wit.

        Returns
        -------
get_prediction
        """
        return self._learner.get_prediction(self._test)

    def predict_class_probabilities(self):
        """Return the probability of every item in the test set to be the positive class.

        Returns
        -------
        Frame
            DataFrame or Sframe containing the probabilities of the test being positive class.
        """
        return self._learner.get_prediction_probabilities(self._test)

    def k_fold_validation(self, k=10):
        """Return k-fold validation results.

        Parameters
        ----------
        k : int
            Number of folds.

        Returns
        -------
        Dict
            Dict contains the AUC
        """
        return self._learner.cross_validate(self._training, k)

    def validate_prediction_by_links(self, result):
        """ Return validation values for anomaly detection
        by link predication.

        Parameters
        ----------
        result : Frame
            The output of classify_by_links_probability can be DataFrame, SFrame.

        Returns
        -------
        Dict
            Dictionary of different metrics such as auc, fpr etc
        """
        return self._learner.validate_prediction_by_links(result)

    def classify_by_links_probability(self, labels={"neg": 0, "pos": 1}):
        """Return the metrics for anomaly detection
        by link predication.

        Parameters
        ----------
        labels : dict, (defual=={"neg": 0, "pos": 1})
            Dictionary containing map of the labels.

        Returns
        -------
        Frame
            DataFrame or SFrame containing the aggregated results.
        """
        probas = self.predict_class_probabilities()
        avg_prob = self._learner.classify_by_links_probability(probas, self._test.features_ids, labels, metadata=self._test.metadata)
        avg_prob = avg_prob.sort("mean_link_label")
        return avg_prob
