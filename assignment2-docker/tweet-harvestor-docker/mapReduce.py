
### team 64 
## Harry Shen 957637 Melbourne
## Jiaqi Wang 908406
## Yisu Ren 1141462
## Chaoyin Chen 1225100


from couchview import CouchView

'''
Reminder: structure of JSON
{"created_at": "Sun May 02 11:24:52 +0000 2021", 
"text": "@im_riya0 I am Bangladeshi. If you are a Bangladeshi you should not bother who is ruling India.  It's not our busin\u2026 https://t.co/e0vCRhip9Q", 
"timestamp_ms": "1619954692968", 
"location": "Adelaide, South Australia", 
"country": "Australia", 
"bounding_box": {"xmin": 138.44213, "ymin": -35.34897, "xmax": 138.78019, "ymax": -34.652564}, 
"sentiment": {"polarity": 0.0, "subjectivity": 0.0}}
'''


class DupCount(CouchView):
    map = '''
    function (doc) {
      emit(doc['id_str'], 1);
    }
    '''

    reduce = '''
        _count
    '''


class CountTotal(CouchView):

    map = '''
    function (doc) {
        emit(doc['country'], 1);
    }
    '''

    reduce = '''
        _sum
    '''


class CitySentiments(CouchView):

    map = '''
    function (doc) {
        emit(doc['location'], doc['polarity']);
    }   
    '''

    reduce = '''
        _stats
        '''


class OverallSentiments(CouchView):

    map = '''
    function (doc) {
        emit(doc['country'], doc['polarity']);
    }
    '''
    reduce = '''
        _stats
    '''


class OverallStateSentiments(CouchView):

    map = '''
    function (doc) {
        emit(doc['state'], doc['polarity']);
    }
    '''
    reduce = '''
        _stats
    '''


class PositiveSentimentPerState(CouchView):

    map = '''
    function (doc) {
        if (doc['polarity'] > 0 && doc['polarity'] < 0.5) {
            emit(doc['state'], 1);
        }
    }       
    '''

    reduce = '''
        _sum
    '''


class NegativeSentimentPerState(CouchView):

    map = '''
    function (doc) {
        if (doc['polarity'] < 0 && doc['polarity'] > -0.5) {
            emit(doc['state'], 1);
        }
    }       
    '''

    reduce = '''
        _sum
    '''


class StrongNegativeSentimentPerState(CouchView):

    map = '''
    function (doc) {
        if (doc['polarity'] <= -0.5) {
            emit(doc['state'], 1);
        }
    }       
    '''

    reduce = '''
        _sum
    '''


class StrongPositiveSentimentPerState(CouchView):

    map = '''
    function (doc) {
        if (doc['polarity'] >= 0.5) {
            emit(doc['state'], 1);
        }
    }       
    '''

    reduce = '''
        _sum
    '''


class NeutralSentimentPerState(CouchView):
    """ Count the number of documents available, per type. """
    map = '''
    function (doc) {
        if (doc['polarity'] == 0) {
            emit(doc['state'], 1);
        }
    }       
    '''

    reduce = '''
        _sum
    '''



class SentiByCityAndDate(CouchView):

    map = '''
    function (doc) {
        emit([doc['date'], doc['state'],doc['city']], doc['polarity']);
    }     
    '''

    reduce = '''
        _stats
    '''

class StateSentiment(CouchView):

    map = '''
    function (doc) {
        emit(doc['state'], doc['polarity']);
    }     
    '''

    reduce = '''
        _stats
    '''

class azView(CouchView):
    map = '''
    function (doc) {
  if (!(doc['tags'].includes('AZ'))) {
      emit(doc['state'], doc['polarity']);
  }
}   
    '''
    reduce = '''
            _stats
        '''


class pzView(CouchView):
    map = '''
    function (doc) {
  if (!(doc['tags'].includes('PZ'))) {
      emit(doc['state'], doc['polarity']);
  }
}
'''
    reduce = '''
            _stats
        '''