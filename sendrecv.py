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

import numpy as np
import Queue
import copy

NUM_PACKETS = 8

class Segment:
    def __init__(self, msg, dst):
        self.msg = msg
        self.dst = dst
        self.seq_bit = -1
        self.seq_num = 0
        
class Buffer(object):
    def __init__(self, size):
        self.size = size
        self.buffer = []
        
    def push(self, item):
        self.buffer.append(item)
        
    def pop(self):
        return self.buffer.pop(0)
        
    def is_full(self):
        return len(self.buffer) == self.size
        
    def is_empty(self):
        return len(self.buffer) == 0

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
        self.has_traffic = False
        self.message_queue = Queue.Queue()

    def receive_from_app(self, msg):
        if self.has_traffic:
            self.message_queue.put(msg)
        else:
            self.has_traffic = True
            self.prepare_segment(msg)

    def receive_from_network(self, seg):
        if AltSender.is_corrupt(seg) or self.has_off_seq_bit(seg):
            self.deliver_seg_to_network()
        else:
            self.update_seq_bit()
            if not self.message_queue.empty():
                self.prepare_segment(self.message_queue.get())
            else:
                self.has_traffic = False

    def prepare_segment(self, msg):
        self.seg = Segment(msg, 'receiver')
        self.seg.seq_bit = self.seq_bit
        self.deliver_seg_to_network()

    def deliver_seg_to_network(self):
        # Send seg to network
        seg_copy = copy.deepcopy(self.seg)
        self.send_to_network(seg_copy)

        # Begin timer
        self.start_timer(self.app_interval)
        
    def on_interrupt(self):
        self.deliver_seg_to_network()

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
            ACK = AltReceiver.make_ACK(seg.msg, self.get_off_seq_bit())
        else:
            # Make ACK and send to client
            ACK = AltReceiver.make_ACK(seg.msg, self.seq_bit)
            
            # Update sequence bit
            self.update_seq_bit()
            
            # Dispaly message to applicaiton layer
            self.send_to_app(seg.msg)

        # Send generated ACK to network
        self.send_to_network(ACK)

    def get_off_seq_bit(self):
        return (self.seq_bit + 1) % 2
            
    def update_seq_bit(self):
        self.seq_bit = (self.seq_bit + 1) % 2
            
    def has_off_seq_bit(self, seg):
        return seg.seq_bit != self.seq_bit

    @staticmethod
    def make_ACK(msg, seq_bit):
        ACK = Segment(msg, 'sender')
        ACK.seq_bit = seq_bit
        return ACK
    
    @staticmethod
    def is_corrupt(seg):
        return seg.msg == '<CORRUPTED>'

class GBNSender(BaseSender):
    def __init__(self, app_interval):
        super(GBNSender, self).__init__(app_interval)
        self.base_number = 1
        self.next_seq_num = 1
        self.packet_sequence = Buffer(NUM_PACKETS)
        self.message_queue = Queue.Queue()
        self.has_traffic = False

    def receive_from_app(self, msg):
        if self.has_traffic:
            self.message_queue.put(msg)
        else:
            seg = self.prepare_segment(msg)
            self.packet_sequence.push(seg)
            self.deliver_to_network(seg)
            
            if self.is_base_seq_next_equal():
                self.start_timer(self.app_interval)
                
            self.next_seq_num += 1
            
            if self.is_packet_sequence_full():
                self.has_traffic = True
        
    def deliver_sequence_to_network(self):
        for seg in self.packet_sequence.buffer:
            self.deliver_to_network(seg) 
    
    def deliver_to_network(self, seg):
        # Make value copy so corruption
        # doesn't mess up the queue
        seg_copy = copy.deepcopy(seg)
        self.send_to_network(seg_copy)
    
    def prepare_segment(self, msg):
        seg = Segment(msg, 'receiver')
        seg.seq_num = self.next_seq_num
        return seg
        
    def receive_from_network(self, seg):
        if not GBNSender.is_corrupt(seg):
            # Ignore unless base number is equal to received seq num
            # We are expecting the receive the right numbered ACK
            if (self.base_number == seg.seq_num):
                self.base_number = seg.seq_num + 1

                # Remove from queue as its been ACK
                self.packet_sequence.pop()
                
                if not self.message_queue.empty():
                    new_seg = self.prepare_segment(self.message_queue.get())
                    self.packet_sequence.push(new_seg)
                    self.next_seq_num += 1
                else:
                    # Number of packets in transition is less than NU
                    self.has_traffic = False
                if self.is_base_seq_next_equal():
                    self.stop_timer()
                else:
                    self.start_timer(self.app_interval)

    def stop_timer(self):
        self.custom_enabled  = False
        self.custom_interval = 0
        self.custom_timer    = 0

    def on_interrupt(self):
        # Begin timer
        self.start_timer(self.app_interval)

        # Send seg to network
        self.deliver_sequence_to_network()

    def is_packet_sequence_full(self):
        return self.packet_sequence.is_full()

    def is_base_seq_next_equal(self):
        return self.next_seq_num == self.base_number

class GBNReceiver(BaseReceiver):
    def __init__(self):
        super(GBNReceiver, self).__init__()
        self.expected_sequence_number = 1
        
    def receive_from_client(self, seg):
        # Make ACK and send to client
        if self.already_received_packet(seg.seq_num):
            ACK = GBNReceiver.make_ACK(seg.msg, seg.seq_num)
        else:
            ACK = GBNReceiver.make_ACK(seg.msg, self.expected_sequence_number)
        
        if not GBNReceiver.is_corrupt(seg) and self.is_expected_sequence_number(seg.seq_num):
            # Update sequence bit
            self.expected_sequence_number += 1
            
            # Dispaly message to applicaiton layer
            self.send_to_app(seg.msg)

        # Send generated ACK to network
        self.send_to_network(ACK)

    def is_expected_sequence_number(self, seq_num):
        return seq_num == self.expected_sequence_number

    def already_received_packet(self, seq_num):
        return self.expected_sequence_number > seq_num

    @staticmethod
    def make_ACK(msg, seq_num):
        ACK = Segment(msg, 'sender')
        ACK.seq_num = seq_num
        return ACK
