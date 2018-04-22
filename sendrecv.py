##
# CSC 216 (Spring 2018)
# Reliable Transport Protocols (Homework 3)
#
# Sender-receiver code for the RDP simulation program.  You should provide
# your implementation for the homework in this file.
#
# Your various Sender implementations should inherit from the BaseSender
# class which exposes the following important methods you should use in your
# implementations:
#
# - sender.send_to_network(seg): sends the given segment to network to be
#   delivered to the appropriate recipient.
# - sender.start_timer(interval): starts a timer that will fire once interval
#   steps have passed in the simulation.  When the timer expires, the sender's
#   on_interrupt() method is called (which should be overridden in subclasses
#   if timer functionality is desired)
#
# Your various Receiver implementations should also inherit from the
# BaseReceiver class which exposes thef ollowing important methouds you should
# use in your implementations:
#
# - sender.send_to_network(seg): sends the given segment to network to be
#   delivered to the appropriate recipient.
# - sender.send_to_app(msg): sends the given message to receiver's application
#   layer (such a message has successfully traveled from sender to receiver)
#
# Subclasses of both BaseSender and BaseReceiver must implement various methods.
# See the NaiveSender and NaiveReceiver implementations below for more details.
##

from sendrecvbase import BaseSender, BaseReceiver

import Queue

class Segment:
    def __init__(self, msg, dst):
        self.msg = msg
        self.dst = dst
        self.seq_bit = -1

class NaiveSender(BaseSender):
    def __init__(self, app_interval):
        super(NaiveSender, self).__init__(app_interval)

    def receive_from_app(self, msg):
        seg = Segment(msg, 'receiver')
        self.send_to_network(seg)

    def receive_from_network(self, seg):
        pass    # Nothing to do!

    def on_interrupt():
        pass    # Nothing to do!

class NaiveReceiver(BaseReceiver):
    def __init__(self):
        super(NaiveReceiver, self).__init__()

    def receive_from_client(self, seg):
        self.send_to_app(seg.msg)

class AltSender(BaseSender):
    def __init__(self, app_interval):
        super(AltSender, self).__init__(app_interval)
        self.seq_bit = 0

    def receive_from_app(self, msg):
        self.seg = Segment(msg, 'receiver')
        self.seg.seq_bit = self.seq_bit
        self.send_to_network(self.seg)
        self.start_timer(self.app_interval)

    def receive_from_network(self, seg):
        if AltSender.is_corrupt(seg) or self.has_off_seq_bit(seg):
            self.send_to_network(self.seg)
        else:
            self.update_seq_bit()
            
    def on_interrupt(self):
        self.send_to_network(self.seg)
        self.start_timer(self.app_interval)

    @staticmethod
    def is_corrupt(seg):
        return seg.msg == '<CORRUPTED>'
    
    def update_seq_bit(self):
        self.seq_bit = (self.seq_bit + 1) % 2
            
    def has_off_seq_bit(self, seg):
        return seg.seq_bit != self.seq_bit

        
class AltReceiver(BaseReceiver):
    def __init__(self):
        super(AltReceiver, self).__init__()
        self.seq_bit = 0

    def receive_from_client(self, seg):
        if AltReceiver.is_corrupt(seg) or self.has_off_seq_bit(seg):
            ACK = AltReceiver.make_ACK(self.get_off_seq_bit())
        else:
            # Make ACK and send to client
            ACK = AltReceiver.make_ACK(self.seq_bit)
            self.send_to_network(ACK)

            # Update sequence bit
            self.update_seq_bit()

            # Dispaly message to applicaiton layer
            self.send_to_app(seg.msg)

    def get_off_seq_bit(self):
        return (self.seq_bit + 1) % 2
            
    def update_seq_bit(self):
        self.seq_bit = (self.seq_bit + 1) % 2
            
    def has_off_seq_bit(self, seg):
        return seg.seq_bit != self.seq_bit

    @staticmethod
    def make_ACK(seq_bit):
        ACK = Segment('ACK', 'sender')
        ACK.seq_bit = seq_bit
        return ACK
    
    @staticmethod
    def is_corrupt(seg):
        return seg.msg == '<CORRUPTED>'

class GBNSender(BaseSender):
    def __init__(self, app_interval):
        pass

    def receive_from_app(self, msg):
        pass

    def receive_from_network(self, seg):
        pass

    def on_interrupt(self):
        pass

class GBNReceiver(BaseReceiver):
    def __init__(self):
        pass

    def receive_from_client(self, seg):
        pass
