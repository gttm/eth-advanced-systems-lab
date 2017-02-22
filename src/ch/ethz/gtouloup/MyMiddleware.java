package ch.ethz.gtouloup;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.logging.FileHandler;
import java.util.logging.Level;
import java.util.logging.Logger;

public class MyMiddleware {
	
	public String myIp = null;
	public int myPort = 0;
	public List<String> mcAddresses = null;
	public int numThreadsPTP = -1;
	public int writeToCount = -1;
	public int virtualNodesNo = 1000;

	public static ConsistentHash consistentHash;
	public List<LinkedBlockingQueue<Request>> writeQueues = new ArrayList<>();
	public List<LinkedBlockingQueue<Request>> readQueues = new ArrayList<>();
	public List<WriteHandler> writeHandlers = new ArrayList<>();
	public List<List<ReadHandler>> readHandlers = new ArrayList<>();
	
	public static Logger myLogger = Logger.getLogger("myLogger");

	public MyMiddleware(String myIp, int myPort, List<String> mcAddresses,int numThreadsPTP, int writeToCount) {
		this.myIp = myIp;
		this.myPort = myPort;
		this.mcAddresses = mcAddresses;
		this.numThreadsPTP = numThreadsPTP;
		this.writeToCount = writeToCount;
		
		myLogger.setLevel(Level.INFO);
		try {
			myLogger.addHandler(new FileHandler("middleware_logger.log"));
		} catch (SecurityException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	public void run() {
		for (int i = 0; i < mcAddresses.size(); i++) {
			consistentHash = new ConsistentHash(virtualNodesNo, mcAddresses);
			writeQueues.add(new LinkedBlockingQueue<Request>());
			readQueues.add(new LinkedBlockingQueue<Request>());
			writeHandlers.add(new WriteHandler(i, writeQueues.get(i), mcAddresses, writeToCount));
			writeHandlers.get(i).start();
			List<ReadHandler> pool = new ArrayList<>();
			for (int j = 0; j < numThreadsPTP; j++) {
				pool.add(new ReadHandler(i, j, readQueues.get(i), mcAddresses.get(i)));
				pool.get(j).start();
			}
			readHandlers.add(pool);
		}
		new NIOServer(myIp, myPort, consistentHash, writeQueues, readQueues, writeHandlers).start();
	}
	
}
