set ns [new Simulator]

#Setting the default prorocols and CBR value
set protocol_1 Tahoe
set protocol_2 Reno
set varyingCBR 1 

if {$argc == 3} {
        set protocol_1 [expr [lindex $argv 0]]
        set protocol_2 [expr [lindex $argv 1]]
        set varyingCBR [expr [lindex $argv 2]]
}

#Setting the link parameters to be used throughout the network and the runtime of the simulation
set link 10Mb
set sDelay 10ms
set lDelay 10ms
set dataFlow 30.0
set programEnd 32.0

set overhead 0

set cbrFlowRate $varyingCBR
append cbrFlowRate mb

#Setting the trace file and the nam file (if required)
set nf [open experiment_2.nam w]
$ns namtrace-all $nf
set filename ./trace/experiment_2
append filename $protocol_1
append filename _
append filename $protocol_2
append filename _
append filename $varyingCBR

set tf [open $filename w]
$ns trace-all $tf

proc finish {} {
        global ns nf tf
        $ns flush-trace 
        close $nf               
        close $tf
        #exec nam experiment_2.nam &
        exit 0
}

#Creating the nodes in the network
set node1 [$ns node]
set node2 [$ns node]
set node3 [$ns node]
set node4 [$ns node]
set node5 [$ns node]
set node6 [$ns node]

#Linking the nodes with specific link parameters
$ns duplex-link $node1 $node2 $link $sDelay DropTail
$ns duplex-link $node5 $node2 $link $sDelay DropTail
$ns duplex-link $node2 $node3 $link $lDelay DropTail
$ns duplex-link $node3 $node4 $link $sDelay DropTail
$ns duplex-link $node3 $node6 $link $sDelay DropTail

#Flow colors (only useful when running the nam file)
$ns color 1 Red 
$ns color 2 Blue
$ns color 3 Black

#Creating a dumbbell network
$ns duplex-link-op $node1 $node2 orient right-down
$ns duplex-link-op $node5 $node2 orient right-up
$ns duplex-link-op $node2 $node3 orient right
$ns duplex-link-op $node3 $node4 orient right-up
$ns duplex-link-op $node3 $node6 orient right-down

#Creating the first TCP agent with the protocol mentioned as parameter
if ([string equal $protocol_1 Tahoe]) {
        set tcpSource_1 [new Agent/TCP]
} else {
        set tcpSource_1 [new Agent/TCP/$protocol_1]
}
$tcpSource_1 set fid_ 1
$tcpSource_1 set class_ 1
$tcpSource_1 set window_ 100
$tcpSource_1 set packetSize_ 1000
$tcpSource_1 set overhead_ $overhead
$ns attach-agent $node1 $tcpSource_1

$tcpSource_1 attach $tf
$tcpSource_1 tracevar cwnd_

#Creating the first TCP Sink
set tcpSink_1 [new Agent/TCPSink]
$ns attach-agent $node4 $tcpSink_1
$ns connect $tcpSource_1 $tcpSink_1  

#Attaching an application to the first TCP source
set tcpStream_1 [new Application/FTP]
$tcpStream_1 attach-agent $tcpSource_1

#Creating the second TCP agent with the protocol mentioned as parameter
if ([string equal $protocol_2 Tahoe]) {
        set tcpSource_2 [new Agent/TCP]
} else {
        set tcpSource_2 [new Agent/TCP/$protocol_2]
}
$tcpSource_2 set fid_ 2
$tcpSource_2 set class_ 2
$tcpSource_2 set window_ 100
$tcpSource_2 set packetSize_ 1000
$tcpSource_2 set overhead_ $overhead
$ns attach-agent $node5 $tcpSource_2


$tcpSource_2 attach $tf
$tcpSource_2 tracevar cwnd_

#Creating the second TCP Sink
set tcpSink_2 [new Agent/TCPSink]
$ns attach-agent $node6 $tcpSink_2
$ns connect $tcpSource_2 $tcpSink_2 

#Creating a UDP agent 
set udpSource [new Agent/UDP]
$udpSource set fid_ 3
$ns attach-agent $node2 $udpSource

#Creating a UDP Sink
set udpSink [new Agent/Null]
$ns attach-agent $node3 $udpSink
$ns connect $udpSource $udpSink

#Attaching an application to the second TCP source
set tcpStream_2 [new Application/FTP]
$tcpStream_2 attach-agent $tcpSource_2

#Attaching an application to the UDP source
set cbrApp [new Application/Traffic/CBR]
$cbrApp set type_ CBR
$cbrApp set packet_size_ 1000
$cbrApp set rate_ $cbrFlowRate
$cbrApp set random_ 1
$cbrApp attach-agent $udpSource

#Starting the first TCP stream
$ns at 0.0 "$tcpStream_1 start"

#Starting the second TCP stream
$ns at 0.0 "$tcpStream_2 start"

#Starting the UDP stream
$ns at 0.0 "$cbrApp start"

#Stopping the UDP stream
$ns at $dataFlow "$cbrApp stop"

#Stopping the first TCP stream
$ns at $dataFlow "$tcpStream_1 stop"

#Stopping the second TCP stream
$ns at $dataFlow "$tcpStream_2 stop"

#Finishing the simulation
$ns at $programEnd "finish"

#Run command to start the simulation
$ns run