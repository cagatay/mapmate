from gaeisha.base import handler
from gaeisha.decorators import require_auth

class view(handler):
    pass

'''
########################## rpcSendMessage ################################    
    @require_auth
    def rpc_send_message(self, args):
        recipient = args['recipient']
        text = args['text']
        response = list()
        sender = self.current_user
        receiver = User.get_by_key_name(recipient)
        
        
        message = Message()
        message.sender = sender
        message.receiver = receiver
        message.text = text
        message.put()
        
        self.sendMessage(recipient, [{ 'type' : 'receivedMessage',
                                      'data' : {
                                                  'from'      : sender.name,
                                                  'date'      : str(message.date),
                                                  'isRead'    : False,
                                                  'text'      : text,
                                                  'senderKey' : sender.id,
                                                  'messageKey': message.key().id()
                                                  }
                                    }])
    
        response.append({
                             'type'    : 'sentMessage',
                             'data'    : {
                                          'to'          : receiver.name,
                                          'date'        : str(message.date),
                                          'text'        : message.text,
                                          'receiverKey' : receiver.id,
                                          'messageKey'  : message.key().id()
                                          }
                             })        
        return response
#############################################################################

    
######################## rpcGetSentMessages #################################
    def rpcGetSentMessages(self, args=None):
        response = list()
        user = self.current_user
        
        if user:
            sentMessages = Message.fetch({
                                          'sender ='        : user,
                                          'senderDeleted =' : False
                                          })
            for message in sentMessages:
                response.append({
                                 'type'    : 'sentMessage',
                                 'data'    : {
                                              'to'          : message.receiver.name,
                                              'date'        : str(message.date),
                                              'text'        : message.text,
                                              'receiverKey' : message.receiver.id,
                                              'messageKey'  : message.key().id()
                                              }
                                 })
        else:
            response.append( { 'type' : 'error' })
        
        return response
#############################################################################


######################## rpcGetReceivedMessages #############################
    def rpcGetReceivedMessages(self):
        response = list()
        
        user = self.current_user
        if user:
            receivedMessages = Message.fetch({
                                              'receiver ='        : user,
                                              'receiverDeleted =' : False
                                            })
            for message in receivedMessages:
                response.append({ 'type' : 'receivedMessage',
                                  'data' : {
                                              'from'      : message.sender.name,
                                              'date'      : str(message.date),
                                              'isRead'    : message.isRead,
                                              'text'      : message.text,
                                              'senderKey' : message.sender.id,
                                              'messageKey': message.key().id()
                                              }
                                 })
        else:
            response.append({'type' : 'error'})
        
        return response
#############################################################################

'''
