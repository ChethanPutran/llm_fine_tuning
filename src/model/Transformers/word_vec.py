import numpy as np

def cosine_similarity(A, B):
    '''
    Input:
        A: a numpy array which corresponds to a word vector
        B: A numpy array which corresponds to a word vector
    Output:
        cos: numerical number representing the cosine similarity between A and B.
    '''

    ### START CODE HERE ###
    dot = np.dot(A,B)    
    norma = np.linalg.norm(A)
    normb = np.linalg.norm(B)    
    cos = dot/(norma*normb)

    ### END CODE HERE ###
    return cos

def get_country(city1, country1, city2, word_embeddings, cosine_similarity=cosine_similarity):
    """
    Input:
        city1: a string (the capital city of country1)
        country1: a string (the country of capital1)
        city2: a string (the capital city of country2)
        word_embeddings: a dictionary where the keys are words and values are their emmbeddings
    Output:
        country: a tuple with the most likely country and its similarity score
    """
    ### START CODE HERE ###

    # store the city1, country 1, and city 2 in a set called group
    group = set([city1, country1,  city2])

    # get embeddings of city 1
    city1_emb = word_embeddings[city1]

    # get embedding of country 1
    country1_emb = word_embeddings[country1]

    # get embedding of city 2
    city2_emb = word_embeddings[city2]

    # get embedding of country 2 (it's a combination of the embeddings of country 1, city 1 and city 2)
    # Remember: King - Man + Woman = Queen
    vec = country1_emb-city1_emb + city2_emb

    # Initialize the similarity to -1 (it will be replaced by a similarities that are closer to +1)
    similarity = -1

    # initialize country to an empty string
    country = ''

    # loop through all words in the embeddings dictionary
    for word in word_embeddings.keys():

        # first check that the word is not already in the 'group'
        if word not in group:

            # get the word embedding
            word_emb = word_embeddings[word]

            # calculate cosine similarity between embedding of country 2 and the word in the embeddings dictionary
            cur_similarity = cosine_similarity(vec,word_emb)

            # if the cosine similarity is more similar than the previously best similarity...
            if cur_similarity > similarity:

                # update the similarity to the new, better similarity
                similarity = cur_similarity

                # store the country as a tuple, which contains the word and the similarity
                country = (word,similarity)

    ### END CODE HERE ###

    return country


def get_accuracy(word_embeddings, data, get_country=get_country):
    '''
    Input:
        word_embeddings: a dictionary where the key is a word and the value is its embedding
        data: a pandas DataFrame containing all the country and capital city pairs

    '''

    ### START CODE HERE ###
    # initialize num correct to zero
    num_correct = 0

    # loop through the rows of the dataframe
    for i, row in data.iterrows():

        # get city1
        city1 = row.city1

        # get country1
        country1 = row.country1

        # get city2
        city2 = row.city2 

        # get country2
        country2 = row.country2 

        # use get_country to find the predicted country2
        predicted_country2, _ = get_country(city1, country1, city2, word_embeddings)

        # if the predicted country2 is the same as the actual country2...
        if predicted_country2 == country2:
            # increment the number of correct by 1
            num_correct += 1

    # get the number of rows in the data dataframe (length of dataframe)
    m = len(data)

    # calculate the accuracy by dividing the number correct by m
    accuracy = num_correct/m

    ### END CODE HERE ###
    return accuracy



def compute_pca(X, n_components=2):
    """
    Input:
        X: of dimension (m,n) where each row corresponds to a word vector
        n_components: Number of components you want to keep.
    Output:
        X_reduced: data transformed in 2 dims/columns + regenerated original data
    pass in: data as 2D NumPy array
    """

    ### START CODE HERE ###
    # mean center the data
    X_demeaned = X-np.mean(X,axis=0)

    # calculate the covariance matrix
    covariance_matrix = np.cov(X_demeaned,rowvar=False)

    # calculate eigenvectors & eigenvalues of the covariance matrix
    eigen_vals, eigen_vecs = np.linalg.eigh(covariance_matrix)

    # sort eigenvalue in increasing order (get the indices from the sort)
    idx_sorted = np.argsort(eigen_vals)
    
    # reverse the order so that it's from highest to lowest.
    idx_sorted_decreasing = idx_sorted[::-1]

    # sort eigenvectors using the idx_sorted_decreasing indices
    eigen_vecs_sorted = eigen_vecs[:,idx_sorted_decreasing]

    # select the first n eigenvectors (n is desired dimension
    # of rescaled data array, or n_components)
    eigen_vecs_subset = eigen_vecs_sorted[:,:n_components]

    # transform the data by multiplying the transpose of the eigenvectors with the transpose of the de-meaned data
    # Then take the transpose of that product. Note that, since for any matrices A, B, (A.B).T = B.T . A.T,
    # this reduces to the dot product of the de-mean data with the eigenvectors
    X_reduced =X_demeaned @ eigen_vecs_subset

    ### END CODE HERE ###

    return X_reduced

def get_vectors(word_embeddings, words):
    """
    Input:
        word_embeddings: a dictionary where the key is a word and the value is its embedding
        words: a list of words for which we want to get the embeddings
    Output:
        X: a numpy array of shape (len(words), 300) where each row corresponds to the embedding of a word in words
    """
    ### START CODE HERE ###
    # create an empty list to store the embeddings
    X = []

    # loop through each word in words
    for word in words:
        # append the embedding of the word to X
        X.append(word_embeddings[word])

    # convert X to a numpy array and return it
    return np.array(X)

    ### END CODE HERE ###

if __name__ == "__main__":
    import pickle
    import pickle
    import numpy as np
    import matplotlib.pyplot as plt

    word_embeddings = pickle.load(open("./data/word_embeddings_subset.p", "rb"))
    len(word_embeddings)  # there should be 243 words that will be used in this assignment

    words = ['oil', 'gas', 'happy', 'sad', 'city', 'town',
         'village', 'country', 'continent', 'petroleum', 'joyful']

    # given a list of words and the embeddings, it returns a matrix with all the embeddings
    X = get_vectors(word_embeddings, words)

    print('You have 11 words each of 300 dimensions thus X.shape is:', X.shape)

    # We have done the plotting for you. Just run this cell.
    result = compute_pca(X, 2)
    plt.scatter(result[:, 0], result[:, 1])
    for i, word in enumerate(words):
        plt.annotate(word, xy=(result[i, 0] - 0.05, result[i, 1] + 0.1))

    plt.show()