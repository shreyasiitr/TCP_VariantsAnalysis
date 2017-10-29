set ns [new Simulator]

#Setting the default prorocol and queueing mechanism
set protocol Reno
set queueTech DropTail 

if {$argc >= 2} {
        set protocol [expr [lindex $argv 0]]
        set queueTech [expr [lindex $argv 1]]
}

#Setting the link parameters to be used throughout the network and the runtime of the simulation
set link 10Mb
set sDelay 10ms
set lDelay 10ms
set dataFlow 30.0
set programEnd 35.0

set cbrFlowRate 3
append cbrFlowRate mb

#Setting the trace file and the nam file (if required)
set nf [open experiment_3.nam w]
$ns namtrace-all $nf
set filename ./trace/experiment_3_
append filename $protocol
append filename _
append filename $queueTech
set tf [open $filename w]
$ns trace-all $tf

proc finish {} {
        global ns nf tf
        $ns flush-trace 
        close $nf               
        close $tf
        #exec nam experiment_3.nam &
        exit 0
}

#Creating the nodes in the network
set node1 [$ns node]
set node2 [$ns node]
set node3 [$ns node]
set node4 [$ns node]
set node5 [$ns node]
set node6 [$ns node]

#Linking the nodes with specific link parameters and the queueing mechanism, which is given as a program parameter
$ns duplex-link $node1 $node2 $link $sDelay $queueTech
$ns duplex-link $node5 $node2 $link $sDelay $queueTech
$ns duplex-link $node2 $node3 $link $lDelay $queueTech
$ns duplex-link $node3 $node4 $link $sDelay $queueTech
$ns duplex-link $node3 $node6 $link $sDelay $queueTech

#Flow colors (only useful when running the nam file)
$ns color 1 Black 
$ns color 2 Red

#Creating a dumbbell network                      
$ns duplex-link-op $node1 $node2 orient right-down
$ns duplex-link-op $node5 $node2 orient right-up
$ns duplex-link-op $node2 $node3 orient right
$ns duplex-link-op $node3 $node4 orient right-up
$ns duplex-link-op $node3 $node6 orient right-down

#Creating a TCP agent with the protocol mentioned as parameter
set tcpSource [new Agent/TCP/$protocol]
$tcpSource set fid_ 1
$tcpSource set window_ 100
$tcpSource set packetSize_ 1000
$ns attach-agent $node1 $tcpSource

$tcpSource attach $tf
#Creating a TCP Sink
set tcpSink [new Agent/TCPSink]
$ns attach-agent $node4 $tcpSink
$ns connect $tcpSource $tcpSink  

#Creating a UDP agent
set udpSource [new Agent/UDP]
$udpSource set fid_ 2
$ns attach-agent $node5 $udpSource

#Creating a UDP Sink
set udpSink [new Agent/Null]
$ns attach-agent $node6 $udpSink
$ns connect $udpSource $udpSink

#Attaching an application to the TCP source
set tcpStream [new Application/FTP]
$tcpStream attach-agent $tcpSource

#Attaching an application to the UDP source
set cbrApp [new Application/Traffic/CBR]
$cbrApp set type_ CBR
$cbrApp set packet_size_ 1000
$cbrApp set rate_ $cbrFlowRate
$cbrApp set random_ 1
$cbrApp attach-agent $udpSource

#Starting the TCP stream
$ns at 0.0 "$tcpStream start"

#Starting the UDP stream
$ns at 10.0 "$cbrApp start"

#Stopping the TCP stream
$ns at $dataFlow "$cbrApp stop"

#Stopping the TCP stream
$ns at $dataFlow "$tcpStream stop"

#Finishing the simulation
$ns at $programEnd "finish"

#Run command to start the simulation
$ns run
