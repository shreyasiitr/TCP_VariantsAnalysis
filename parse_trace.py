import matplotlib.pyplot as plt
import numpy as np
import sys

n1 = 1
n2 = 2
n3 = 3
n4 = 4
n5 = 5
n6 = 6


def parseLine(line):
    split = line.split()
    if len(split) == 12:
        return {
            'type': split[0],
            'time': float(split[1]),
            'src': int(split[2]),
            'dst': int(split[3]),
            'bytes': float(split[5]) * 8,
            'fid': int(split[7])
        }
    else:
        return False


# subroutine to test out the plotting functionality
def plot(labels, x_axis, y_axis, title, x_title, y_title, colour, maximum_y, label, minimum_y):
    # Plot a line graph
    plt.figure(title, figsize=(18, 8))
    plt.grid(True)  # Turn the grid on
    plt.ylabel(y_title)  # Y-axis label
    plt.xlabel(x_title)  # X-axis label
    plt.title(x_title + ' vs ' + y_title)  # Plot title
    plt.xlim(0, max(x_axis)+2)  # set x axis range
    if minimum_y < 0:
        minimum_y = 0
    plt.ylim(minimum_y, maximum_y)  # Set yaxis range

    if colour:
        plt.plot(x_axis, y_axis, colour, linewidth=3, label=label)
    else:
        plt.plot(x_axis, y_axis, linewidth=3, label=label)
    plt.legend(labels, loc='best')
    return


def parseTraceFile(path, fid, src, dst, interval_length, bandwidth, basertt, file_name):
    trace = open(path, 'r')     # open the trace file
    length_queue = 0            # tracks the length of the queue
    time_last_packet = 0        # tracks the last packet received time
    bytes_current_interval = 0  # tracks the bytes received in the current interval
    bytes_total = 0             # tracks the total number of bytes received
    throughput_interval = 0     # the throughput observed in the current interval
    bandwidth *= 1e6            # from mbps to bps
    total_delay = 0
    count_delay = 0
    count_drop = 0
    start_time = 0
    last = 0
    rtt_over_time = []
    rtt_time = []
    throughput_over_time = []
    throughput_time = []
    drop_rate_over_time = []
    drop_rate_time = []
    last_rtt_time = 0
    interval_count_delay = 0

    for line in trace:                  # iterate over all the lines in the trace file
        parsedline = parseLine(line)    # parse the line from trace file
        if parsedline:
            if parsedline['src'] == src and parsedline['dst'] == dst and parsedline['bytes'] >= 8000:
                if parsedline['type'] == 'd':               # drop encountered
                    length_queue -= parsedline['bytes']     # decrease the queue to account for the drop
                if parsedline['type'] == '+':               # enqueue encountered
                    length_queue += parsedline['bytes']     # increase the queue to account for the enqueue
                if parsedline['type'] == '-':               # encountered a dequeue
                    length_queue -= parsedline['bytes']     # decrease the length of the packet

                if parsedline['fid'] == fid:                    # if the flowID is what we are tracking
                    bytes_total += parsedline['bytes']          # increment the total bytes received
                    if parsedline['type'] == 'r':               # handle receive event
                        last = parsedline['time']
                        if start_time == 0:                     # the start of the receiving stream
                            start_time = parsedline['time']
                        if parsedline['time'] < time_last_packet + interval_length:
                            # if the packet is received within the interval we are tracking
                            bytes_current_interval += parsedline['bytes']
                            # increment the bytes received in this interval
                        else:
                            # calculate throughput
                            time_last_packet = parsedline['time']
                            throughput_over_time.append(bytes_current_interval / (1e6*interval_length))
                            throughput_time.append(parsedline['time'])
                            bytes_current_interval = parsedline['bytes']
                            bytes_total += parsedline['bytes']
                            drop_rate_over_time.append(count_drop)
                            drop_rate_time.append(parsedline['time'])
                    elif parsedline['type'] == '+' or parsedline['type'] == '-' or parsedline['type'] == 'd':
                        delay_queue = length_queue / bandwidth
                        rtt = basertt + delay_queue
                        total_delay += rtt
                        count_delay += 1
                        interval_count_delay += 1
                        if parsedline['time'] > last_rtt_time + interval_length:
                            rtt_over_time.append((rtt*1000 / interval_count_delay))
                            rtt_time.append(parsedline['time'])
                            last_rtt_time = parsedline['time']
                            interval_count_delay = 0
                        if parsedline['type'] == 'd':
                            count_drop += 1

    if (last-start_time) != 0:
        throughput_average = bytes_total / (1e7*(last - start_time))
    else:
        throughput_average = 0

    packet_drop_rate = count_drop
    print('Average Throughput for '+file_name+':' + str(throughput_average))
    rtt_average = total_delay / count_delay
    print('Average RTT for '+file_name+':' + str(rtt_average))
    return {
        'rtt_average': rtt_average,
        'throughput_average': throughput_average,
        'packet_drop_rate': packet_drop_rate,
        'rtt_time': rtt_time,
        'rtt_over_time': rtt_over_time,
        'throughput_over_time': throughput_over_time,
        'throughput_time': throughput_time,
        'drop_rate_over_time': drop_rate_over_time,
        'drop_rate_time': drop_rate_time
    }

protocols = {
    'experiment_1': {
        'protocols': ['Reno', 'Tahoe', 'Newreno', 'Vegas'],
        'colours': {
            'Tahoe': 'r',
            'Reno': 'b',
            'Newreno': 'g',
            'Vegas': 'c'
        }
    },
    'experiment_2': {
        'protocols': ['Newreno_Reno', 'Newreno_Vegas', 'Reno_Reno', 'Vegas_Vegas'],
        'colours': {
            1: 'r',
            2: 'b'
        }
    },
    'experiment_3': {
        'protocols': ['Reno_RED', 'Sack1_DropTail', 'Sack1_RED', 'Reno_DropTail'],
        'colours': {
            'Reno_DropTail': 'r',
            'Reno_RED': 'b',
            'Sack1_DropTail': 'g',
            'Sack1_RED': 'c'
        }
    }
}


def experiment_1(args, protocolss, cbr_rates, basertt, fid):
    labels = []

    for protocol in protocolss:
        rtt_average = []
        throughput_average = []
        drop_rate = []
        rtt_maximum_y = -1
        throughput_maximum_y = -1
        drop_rate_maximum_y = -1
        rtt_minimum_y = 2 ^ 32
        throughput_minimum_y = 2 ^ 32
        drop_rate_minimum_y = 2 ^ 32
        labels.append(protocol)

        for cbr in cbr_rates:
            file_name = 'trace/'+args+protocol+'_'+str(cbr)
            result = parseTraceFile(file_name, fid, n1, n2, 0.5*1e6, 10, basertt, file_name)
            rtt_average.append(result['rtt_average'])
            throughput_average.append(result['throughput_average'])
            drop_rate.append(result['packet_drop_rate'])
            if throughput_maximum_y < max(throughput_average):
                throughput_maximum_y = max(throughput_average) + 5
            if rtt_maximum_y < max(rtt_average):
                rtt_maximum_y = max(rtt_average) + 0.05
            if drop_rate_maximum_y < max(drop_rate):
                drop_rate_maximum_y = max(drop_rate) + 150

            if throughput_minimum_y > min(throughput_average):
                throughput_minimum_y = min(throughput_average) - 5
            if rtt_minimum_y > min(rtt_average):
                rtt_minimum_y = min(rtt_average) - 0.05
            if drop_rate_minimum_y > min(drop_rate):
                drop_rate_minimum_y = min(drop_rate) - 150

        # plot rtt over cbr rates
        plot(labels, cbr_rates, rtt_average, args + ' RTT '+'flow: '+str(fid), 'CBR(Mbps)', 'RTT(s)', protocols[args]['colours'][protocol], rtt_maximum_y, protocol, rtt_minimum_y)
        # plot throughput over cbr rates
        plot(labels, cbr_rates, throughput_average, args+' Throughput(Mbps) '+'flow:'+str(fid), 'CBR(Mbps)', 'Throughput(Mbps)',
                        protocols[args]['colours'][protocol], throughput_maximum_y, protocol, throughput_minimum_y)
        # plot drop rate over cbr rates
        plot(labels, cbr_rates, drop_rate, args + ' Number of Packets Dropped '+'flow:'+str(fid), 'CBR(Mbps)', 'Drop Rate(per second)', protocols[args]['colours'][protocol],
             drop_rate_maximum_y, protocol, drop_rate_minimum_y)

    # Displays the plots.
    # You must close the plot window for the code following each show()
    # to continue to run
    # plt.show()
    plt.savefig('Figures/experiment1')
    return


def experiment_2(args, protocolss, cbr_rates, basertt, fids):
    rtt_maximum_y = -1
    throughput_maximum_y = -1
    drop_rate_maximum_y = -1
    rtt_minimum_y = 2 ^ 32
    throughput_minimum_y = 2 ^ 32
    drop_rate_minimum_y = 2 ^ 32

    for fid in fids:
        for protocol in protocolss:
            rtt_average = []
            throughput_total_average = 0
            throughput_average = []
            drop_rate = []
            labels = protocol.split('_')
            for cbr in cbr_rates:
                file_name = 'trace/' + args + protocol + '_' + str(cbr)
                result = parseTraceFile(file_name, fid, n1, n2, 0.5, 10, basertt, file_name)
                rtt_average.append(result['rtt_average'])
                throughput_average.append(result['throughput_average'])
                throughput_total_average += result['throughput_average']
                drop_rate.append(result['packet_drop_rate'])
                if throughput_maximum_y < max(throughput_average):
                    throughput_maximum_y = max(throughput_average) + 5
                if rtt_maximum_y < max(rtt_average):
                    rtt_maximum_y = max(rtt_average) + 0.05
                if drop_rate_maximum_y < max(drop_rate):
                    drop_rate_maximum_y = max(drop_rate) + 20

                if throughput_minimum_y > min(throughput_average):
                    throughput_minimum_y = min(throughput_average) - 20
                if rtt_minimum_y > min(rtt_average):
                    rtt_minimum_y = min(rtt_average) - 0.05
                if drop_rate_minimum_y > min(drop_rate):
                    drop_rate_minimum_y = min(drop_rate) - 120

            # plot rtt over cbr rates
            plot(labels, cbr_rates, rtt_average, args + ' RTT '+' for '+protocol, 'CBR(Mbps)', 'RTT(s)',
                 protocols[args]['colours'][fid], rtt_maximum_y, fid, rtt_minimum_y)
            # plot throughput over cbr rates
            plot(labels, cbr_rates, throughput_average, args + ' Throughput(Mbps) '+' for '+protocol, 'CBR(Mbps)',
                 'Throughput(Mbps)',
                    protocols[args]['colours'][fid], throughput_maximum_y, fid, throughput_minimum_y)
            # plot drop rate over cbr rates
            plot(labels, cbr_rates, drop_rate, args + ' Number of Packets Dropped '+' for '+protocol, 'CBR(Mbps)',
                 'Drop Rate(per second)', protocols[args]['colours'][fid],
                drop_rate_maximum_y, fid, drop_rate_minimum_y)

            print 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'
            print 'for fid:'+str(fid)+' protocol:'+ protocol+' throughput:'+str(throughput_total_average/len(cbr_rates))
            print 'XXXXXXXXXXXXXXXXXXXXXXXXXXXX'

    # Displays the plots.
    # You must close the plot window for the code following each show()
    # to continue to run
    # plt.show()
    plt.save('Figures/experiment2')
    return


def experiment_3(basertt, fid=1):
    labels = []
    rtt_maximum = -1
    rtt_minimum = 2^32
    throughput_maximum = -1
    throughput_minimum = 2 ^ 32

    for file_name in protocols['experiment_3']['protocols']:
        labels.append(file_name)
        file_title = 'trace/experiment_3_'+file_name
        result = parseTraceFile(file_title, fid, n1, n2, 1, 10, basertt, file_title)
        if min(result['rtt_over_time']) < rtt_minimum:
            rtt_minimum = min(result['rtt_over_time'])
        if max(result['rtt_over_time']) > rtt_maximum:
            rtt_maximum = max(result['rtt_over_time'])
        if min(result['throughput_over_time']) < throughput_minimum:
            throughput_minimum = min(result['throughput_over_time'])
        if max(result['throughput_over_time']) > throughput_maximum:
            throughput_maximum = max(result['throughput_over_time'])

        plot(labels, result['rtt_time'], result['rtt_over_time'], 'experiment_3_RTT', 'Time', 'RTT(s)',
             protocols['experiment_3']['colours'][file_name], rtt_maximum, file_name,
             rtt_minimum)
        plot(labels, result['throughput_time'], result['throughput_over_time'], 'experiment_3_Throughput', 'Time',
             'Throughput(Mbps)',
             protocols['experiment_3']['colours'][file_name], throughput_maximum+1, file_name,
             throughput_minimum-1)
    #plt.show()
    plt.save('Figures/experiment3')
    return


if len(sys.argv) > 1:
    if sys.argv[1] == '1':
        experiment_1('experiment_1', protocols['experiment_1']['protocols'], list(np.arange(1, 10.5, 0.5)), 6 * 0.01, 1)
    elif sys.argv[1] == '2':
        experiment_2('experiment_2', protocols['experiment_2']['protocols'], list(np.arange(1, 10.5, 0.5)), 6 * 0.01,
                 [1, 2])
    elif sys.argv[1] == '3':
        experiment_3(6 * 0.01)
else:
    # if no arguments are specified then run all the experiments
    experiment_1('experiment_1', protocols['experiment_1']['protocols'], list(np.arange(1, 10.5, 0.5)), 6 * 0.01, 1)
    experiment_2('experiment_2', protocols['experiment_2']['protocols'], list(np.arange(1, 10.5, 0.5)), 6 * 0.01,
                 [1, 2])
    experiment_3(6 * 0.01)
