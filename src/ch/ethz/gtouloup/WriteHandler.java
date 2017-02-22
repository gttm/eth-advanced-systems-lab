package ch.ethz.gtouloup;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.SocketChannel;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.LinkedBlockingQueue;

public class WriteHandler extends Thread {
	
	private int mcServerNo;
	private int writeToCount;
	private LinkedBlockingQueue<Request> writeQueue;
	private Request request;
	
	private int[] replicationServers;
	private Map<String, Integer> inetToMcNoMap = new HashMap<String, Integer>();
	private List<String> mcInetAddresses = new ArrayList<>();
	private List<LinkedList<Request>> responseQueues = new ArrayList<>();
	private Selector selector;
	private List<SocketChannel> clients = new ArrayList<>();
	private final int BUFFERSIZE = 8192;
	private ByteBuffer buffer = ByteBuffer.allocate(BUFFERSIZE);
	
	private final int SAMPLINGRATE = 100;
	private int count = 0;

	public WriteHandler(int mcServerNo, LinkedBlockingQueue<Request> writeQueue, List<String> mcAddresses, int writeToCount) {
		this.mcServerNo = mcServerNo;
		this.writeQueue = writeQueue;
		this.replicationServers = new int[mcAddresses.size()];
		this.writeToCount = writeToCount;
		
		try {
			selector = Selector.open();
			for (int i = 0; i < writeToCount; i++) {
				responseQueues.add(new LinkedList<Request>());
				replicationServers[i] = ((mcServerNo + i)%mcAddresses.size());			
				String[] mcAddressPort = mcAddresses.get(replicationServers[i]).split(":");
				InetSocketAddress mcInetAddress = new InetSocketAddress(mcAddressPort[0], Integer.parseInt(mcAddressPort[1]));
				inetToMcNoMap.put(mcInetAddress.toString(), replicationServers[i]);
				mcInetAddresses.add(mcInetAddress.toString());
				SocketChannel client = SocketChannel.open(mcInetAddress);
				client.configureBlocking(false);
				client.register(selector, SelectionKey.OP_READ);				
				clients.add(client);
				//System.out.println("WriterHandler " + mcServerNo + ", replica " + replicationServers[i] + " connected to memcached at " + 
				//		mcAddresses.get(replicationServers[i]) + ": " + mcAddressPort[0] + " " + Integer.parseInt(mcAddressPort[1]));
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	
	public void notifyWriteHandler() {
		selector.wakeup();
	}
	
	public void run() {
		while (true) {
			try {
				while (!writeQueue.isEmpty()) {
					write();
				}
				
				selector.select();				
				Iterator<SelectionKey> selectedKeys = selector.selectedKeys().iterator();
				while (selectedKeys.hasNext()) {
					SelectionKey key = selectedKeys.next();
					selectedKeys.remove();
					
					if (key.isReadable()) {
						read(key);
					}
				}
			} catch (Exception e) {
				e.printStackTrace();
			}
		}
	}
	
	private void write() throws InterruptedException, IOException {
		request = writeQueue.take();
		request.tQueue = (System.nanoTime() - request.tQueue)/1000;
		//System.out.println("WriterHandler " + mcServerNo + " received request: " + new String(request.message));
		
		// send request to memcached servers
		request.tServer = System.nanoTime();
		for (int i = 0; i < writeToCount; i++) {					
			buffer.clear();
			buffer.put(request.message);
			buffer.flip();
			while (buffer.hasRemaining()) {
				clients.get(i).write(buffer);
			}
			responseQueues.get(i).add(request);
		}
		request.tWrite = (System.nanoTime() - request.tServer)/1000;
		//System.out.println("WriterHandler sent the message and its replicas to memcached servers");		
	}
	
	private void read(SelectionKey key) throws IOException {
		long tWriteAdd = System.nanoTime();
		SocketChannel client = (SocketChannel) key.channel();
		buffer.clear();
		
		int numRead = client.read(buffer);
		long tResponse = System.nanoTime();

		byte[] responseRaw = new byte[numRead];
	    System.arraycopy(buffer.array(), 0, responseRaw, 0, numRead);
		
		// we may have read multiple responses
	    //if (numRead > 12) System.out.println("Big response!");
		//System.out.println("Memcached server " + inetToMcNoMap.get(client.getRemoteAddress().toString()) + " raw response: >>> " + new String(responseRaw) + " <<<");
		String[] responses = new String(responseRaw).split("\r\n");		
		for (String responseStr : responses) {
			byte[] response = (responseStr + "\r\n").getBytes();
			request = responseQueues.get(mcInetAddresses.indexOf(client.getRemoteAddress().toString())).remove();
			request.responses.add(response);
			request.tWrite += (System.nanoTime() - tWriteAdd)/1000;
			if (request.responses.size() == writeToCount) {
				tWriteAdd = System.nanoTime();
				request.tServer = (tResponse - request.tServer)/1000;
				// check responses, return error to client in case they differ, otherwise forward the common response
				buffer.clear();
				buffer.put(request.responses.get(0));
				//System.out.print("Received responses: \n" + new String(request.responses.get(0)));
				for (int i = 1; i < writeToCount; i++) {
					//System.out.print(new String(request.responses.get(i)));
					if (!Arrays.equals(request.responses.get(0), request.responses.get(i))) {
						buffer.clear();
						buffer.put("SERVER_ERROR replication error\r\n".getBytes());
						//System.out.println("Send SERVER_ERROR to client");
						request.fSuccess = 0;
						break;
					}
				}
				
				// check if the request succeeded
				if (!responseStr.startsWith("STORED")&&!responseStr.startsWith("DELETED")) {
					request.fSuccess = 0;
				}
				
				// send memcached response to the client
				buffer.flip();
				while (buffer.hasRemaining()) {
					request.requestClient.write(buffer);
				}
				request.tWrite += (System.nanoTime() - tWriteAdd)/1000;
				request.tMW = (System.nanoTime() - request.tMW)/1000;
				
				// sample log metrics
				if (count++%SAMPLINGRATE == 0) {					
					String logMessage = String.format("%d, %d, %d, %d, %d, %d", request.fSuccess, request.tMW, request.tQueue, request.tServer, request.tHash, request.tWrite);
					MyMiddleware.myLogger.info(logMessage);
				}
			}	
		}
	}
	
}
