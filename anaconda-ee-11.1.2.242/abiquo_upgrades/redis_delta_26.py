from subprocess import *
import urlparse

HOST = "localhost"
PORT = 6379
SPORT = str(PORT)
 
# Ping!
ret = call(["redis-cli", "-h", HOST, "-p", SPORT, "PING"], stdout=PIPE)
 
if ret:
    print("Unable to connect redis at", HOST, ":", SPORT)
    exit(1)
 
# Retrieve all monitors
cmd = Popen("redis-cli -h %s -p %d smembers PhysicalMachine:all" % (HOST, PORT), shell=True, stdout=PIPE)
 
for pm in cmd.stdout:
    print("PM: %s" % pm)
    key = "PhysicalMachine:%s" % (pm.strip())

    # Get address and monitor type
    address = Popen(["redis-cli", "--raw", "-h", HOST, "-p", SPORT, "hget", key, "address"], stdout=PIPE).communicate()[0].strip()
    monitorType = Popen(["redis-cli", "--raw", "-h", HOST, "-p", SPORT, "hget", key, "type"], stdout=PIPE).communicate()[0].strip()

    # Delete unused fields
    call(["redis-cli", "-h", HOST, "-p", SPORT, "hdel", key, "address"], stdout=PIPE)

    # Insert new fields
    url = urlparse.urlparse(address)

    ip = url.hostname
    port = str(url.port)
    agentPort = ""

    if (monitorType == "KVM") or (monitorType == "XEN"):
        agentPort = port
        port = ""

    call(["redis-cli", "-h", HOST, "-p", SPORT, "hset", key, "ip", ip], stdout=PIPE)
    call(["redis-cli", "-h", HOST, "-p", SPORT, "hset", key, "port", port], stdout=PIPE)
    call(["redis-cli", "-h", HOST, "-p", SPORT, "hset", key, "manager_ip", ""], stdout=PIPE)
    call(["redis-cli", "-h", HOST, "-p", SPORT, "hset", key, "manager_port", ""], stdout=PIPE)
    call(["redis-cli", "-h", HOST, "-p", SPORT, "hset", key, "agent_ip", ""], stdout=PIPE)
    call(["redis-cli", "-h", HOST, "-p", SPORT, "hset", key, "agent_port", agentPort], stdout=PIPE)

    # Update index by address
    old_index_key = "PhysicalMachine:address:%s" % (address)
    new_index_key = "PhysicalMachine:address:%s" % (ip)
    call(["redis-cli", "-h", HOST, "-p", SPORT, "sunionstore", new_index_key, old_index_key], stdout=PIPE)
    call(["redis-cli", "-h", HOST, "-p", SPORT, "del", old_index_key], stdout=PIPE)
