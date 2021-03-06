import os.path
import pickle

import numpy as np
from sklearn import datasets
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor

import DBInteract


class PredictQuery:
    """predictQuery class - Predict number of query results returned"""

    def __init__(self, nn_only=False):
        """predictQuery constructor"""
        self.models = {"linreg": None, "knn": None, "rf": None, "nn_class": None, "nn": None}
        if os.path.isfile("app/TestData/linreg_model.p") and (not nn_only):
            self.models["linreg"] = pickle.load( open("app/TestData/linreg_model.p", "rb"))
        if os.path.isfile("app/TestData/knn_model.p") and (not nn_only):
            self.models["knn"] = pickle.load( open("app/TestData/knn_model.p", "rb"))
        if os.path.isfile("app/TestData/rf_model.p") and (not nn_only):
            self.models["rf"] = pickle.load( open("app/TestData/rf_model.p", "rb"))
        if os.path.isfile("app/TestData/nn_class_model.p"):
            self.models["nn_class"] = pickle.load( open("app/TestData/nn_class_model.p", "rb"))
        if os.path.isfile("app/TestData/nn_model.p"):
            self.models["nn"] = pickle.load( open("app/TestData/nn_model.p", "rb"))

    def train(self, X, y, linreg=True, knn=True, rf=True, nn_class=True, nn=True, k=3, knn_weights="uniform", num_trees=10, max_depth=None, min_res=10):
        """
        Trains indicated models. By default, trains none.
        :param X: Training data features
        :param y: Training data targets
        :param linreg: Flag indicating whether or not linear regression model should be trained
        :param knn: Flag indicating whether or not k-nearest neighbors model should be trained
        :param rf: Flag indicating whether or not random forest model should be trained
        :param k: Number of NN to use in model
        :param knn_weights: How to weight the nearest neighbors. Check out sklearn for options
        :param num_trees: Number of trees in the forest
        :param max_depth: Max depth of any tree in the forest
        :return: None
        """
        if linreg:
            self.train_linreg(X, y)
            pickle.dump(self.models["linreg"], open("app/TestData/linreg_model.p", "wb"))
            print "finished training linreg"
        if knn:
            self.train_knn(X, y, k=k, weights=knn_weights)
            pickle.dump(self.models["knn"], open("app/TestData/knn_model.p", "wb"))
            print "finished training knn"
        if rf:
            self.train_rf(X, y, num_trees=num_trees, max_depth=max_depth)
            pickle.dump(self.models["rf"], open("app/TestData/rf_model.p", "wb"))
            print "finished training rf"
        if nn_class:
            y_class = np.zeros(y.shape)
            y_class[y >= 2*min_res] = 1
            self.train_nn_class(X, y_class)
            pickle.dump(self.models["nn_class"], open("app/TestData/nn_class_model.p", "wb"))
            print "finished training nn classifier"
        if nn:
            self.train_nn(X, y)
            pickle.dump(self.models["nn"], open("app/TestData/nn_model.p", "wb"))
            print "finished training nn"

    def train_linreg(self, X, y):
        """
        Trains linear regression model
        :param X: Training data features
        :param y: Training data targets
        :return: Handle to linear regression model
        """
        lr = LinearRegression()
        lr.fit(X, y)
        self.models["linreg"] = lr
        return lr

    def train_knn(self, X, y, k=3, weights="uniform"):
        """
        Trains k nearest neighbor model
        :param X: Training data features
        :param y: Training data targets
        :param k: Number of NN to use in model
        :param weights: How to weight the nearest neighbors. Check out sklearn for options
        :return: Handle to knn model
        """
        knn = KNeighborsRegressor(n_neighbors=k, weights=weights)
        knn.fit(X, y)
        self.models["knn"] = knn
        return knn

    def train_rf(self, X, y, num_trees=10, max_depth=None):
        """
        Trains random forest model
        :param X: Training data features
        :param y: Training data targets
        :param num_trees: Number of trees in the forest
        :param max_depth: Max depth of any tree in the forest
        :return: handle to random forest model
        """
        rf = RandomForestRegressor(n_estimators=num_trees, max_depth=max_depth)
        rf.fit(X, y)
        self.models["rf"] = rf
        return rf

    def train_nn_class(self, X, y, min_res=10):
        """
        Trains neural network model
        :param X: Training data features
        :param y: Training data targets
        :return: handle to neural net model
        """
        nn = MLPClassifier(hidden_layer_sizes=(100, 50, 25), max_iter=200, verbose=True)
        nn.fit(X, y)
        self.models["nn_class"] = nn
        return nn

    def train_nn(self, X, y):
        """
        Trains neural network model
        :param X: Training data features
        :param y: Training data targets
        :return: handle to neural net model
        """
        nn = MLPRegressor(hidden_layer_sizes=(200, 50, 25), max_iter=200, verbose=True)
        nn.fit(X, y)
        self.models["nn"] = nn
        return nn

    def test(self, X, y, reg=True, min_res=10):
        """
        Tests models
        :param X: Testing data features
        :param y: Testing data targets
        :return: None
        """
        if reg:
            for key in self.models:
                if key == "nn_class":
                    continue
                if self.models[key] is not None:
                    print "Beginning to test model: {}".format(key)
                    pred = self.models[key].predict(X)
                    rmse = np.sqrt(mean_squared_error(y, pred))
                    print "Model", key, "yields RMSE = ", rmse
        else:
            y[y < 2*min_res] = 0
            y[y >= 2*min_res] = 1
            pred = self.models["nn_class"].predict(X)
            err_rate = 1.0 - (float(np.sum(pred == y)) / y.shape[0])
            fp = pred[(pred != y) & (pred==1)].shape[0]
            fn = pred[(pred != y) & (pred==0)].shape[0]
            tp = pred[(pred == y) & (pred == 1)].shape[0]
            tn = pred[(pred == y) & (pred == 0)].shape[0]
            print "Model nn_class yields Error Rate = {}, tp = {}, tn = {}, fp = {}, fn = {}".format(err_rate, tp, tn, fp, fn)

def build_training_data(ingredient_info, big=False, verbose=True):
    """
    Generates training samples and target values
    :return: (training features, training targets)
    """
    if verbose:
        print "Building Training Data"
    # set up variables
    ret_X = []
    db_queries = []
    ret_y = []
    num_ingred = 2140
    dbi = DBInteract.DBInteract()
    dbi.connect_to_db()

    # set up necessary LUT
    feat_to_id = {}
    for ing_id in ingredient_info.keys():
        feat_num = ingredient_info[ing_id]["feature number"]
        feat_to_id[feat_num] = ing_id

    # build queries and data
    if not big:
        samples_per = 2000
    else:
        samples_per = 100000
    choices = range(num_ingred)
    for k in range(1, 11):
        if k == 1:
            samples = 3000
        else:
            samples = samples_per
        for _ in range(1, samples+1):
            new_ingreds = np.random.choice(choices, k)
            # get feature data
            new_feat = np.zeros(num_ingred)
            new_feat[new_ingreds] = 1
            ret_X.append(new_feat)
            # get target data
            db_queries.append([feat_to_id[x] for x in new_ingreds])
            db_result = dbi.get_recipes(db_queries[-1])
            ret_y.append(len(db_result))
        if verbose:
            print "Finished building k = {} samples".format(k)

    ret_X = np.array(ret_X)
    ret_y = np.array(ret_y)
    if not big:
        np.save("app/TestData/predict_query_train_X", ret_X)
        np.save("app/TestData/predict_query_train_y", ret_y)
    else:
        np.save("app/TestData/predict_query_train_X_big", ret_X)
        np.save("app/TestData/predict_query_train_y_big", ret_y)
    return ret_X, ret_y

def test_on_db_data(big=False):
    """
    Tests regression models on generated test data
    :return: None
    """
    from LookUpTables import create_ingredient_info, create_group_info
    group_info, ingred_to_group = create_group_info()
    ingredient_info = create_ingredient_info(ingred_to_group)

    # load or generate file
    if os.path.isfile("app/TestData/predict_query_train_X.npy") and (big == False):
        all_X = np.load("app/TestData/predict_query_train_X.npy")
        all_y = np.load("app/TestData/predict_query_train_y.npy")
    elif os.path.isfile("app/TestData/predict_query_train_X_big.npy") and (big == True):
        all_X = np.load("app/TestData/predict_query_train_X_big.npy")
        all_y = np.load("app/TestData/predict_query_train_y_big.npy")
    else:
        all_X, all_y = build_training_data(ingredient_info, big=False)

    # shuffle data
    all_data = np.c_[all_X, np.reshape(all_y, (all_y.shape[0], 1))]
    np.random.shuffle(all_data)

    # split training data
    n_train = int(0.8 * all_data.shape[0])
    train_X = all_data[0:n_train, 0:all_data.shape[1]-1]
    train_y = all_data[0:n_train, -1]

    test_X = all_data[n_train:, 0:all_data.shape[1]-1]
    test_y = all_data[n_train:, -1]

    # train
    pq = PredictQuery()
    # pq.train(train_X, train_y, linreg=False, knn=False, rf=False, nn_class=False, nn=False, k=3, num_trees=10, max_depth=2)

    # test
    # print "Testing in-sample"
    # pq.test(train_X, train_y, reg=False)
    print "\nTesting out-of-sample"
    pq.test(test_X, test_y, reg=False)

def test_on_diabetes():
    """
    Tests regression models on sklearn diabetes dataset
    :return: None
    """
    # load dataset
    diabetes = datasets.load_diabetes()

    # get features data
    diabetes_X = diabetes.data[:, np.newaxis, 2]
    diabetes_X_train = diabetes_X[:-20]
    diabetes_X_test = diabetes_X[-20:]

    # get target values
    diabetes_y_train = diabetes.target[:-20]
    diabetes_y_test = diabetes.target[-20:]
    pq = PredictQuery()

    # train models
    # pq.train(diabetes_X_train, diabetes_y_train, linreg=False, knn=False, rf=False, k=10, num_trees=100)

    # test models
    pq.test(diabetes_X_test, diabetes_y_test)

if __name__ == "__main__":
    # test_on_diabetes()
    test_on_db_data(big=False)
