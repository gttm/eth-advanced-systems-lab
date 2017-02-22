package ch.ethz.gtouloup;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.SocketChannel;
import java.util.concurrent.LinkedBlockingQueue;

public class ReadHandler extends Thread {
	
	private int mcServerNo;
	private int poolNo;
	private LinkedBlockingQueue<Request> readQueue;
	private Request request;
	
	private SocketChannel client;
	private final int BUFFERSIZE = 2048;
	private ByteBuffer buffer = ByteBuffer.allocate(BUFFERSIZE);
	
	private final int SAMPLINGRATE = 100;
	private int count = 0;

	public ReadHandler(int mcServerNo, int poolNo, LinkedBlockingQueue<Request> readQueue, String mcAddressStr) {
		this.mcServerNo = mcServerNo;
		this.poolNo = poolNo;
		this.readQueue = readQueue;
		
		String[] mcAddressPort = mcAddressStr.split(":");
		InetSocketAddress mcAddress = new InetSocketAddress(mcAddressPort[0], Integer.parseInt(mcAddressPort[1]));
		try {
			this.client = SocketChannel.open(mcAddress);
			//System.out.println("ReadHandler " + mcServerNo + "," + poolNo + " connected to memcached at " + 
			//		mcAddressStr + ": " + mcAddressPort[0] + " " + Integer.parseInt(mcAddressPort[1]));
		} catch (IOException e) {
			e.printStackTrace();
		}
	}
	
	public void run() {
		while (true) {
			try {
				request = readQueue.take();
				request.tQueue = (System.nanoTime() - request.tQueue)/1000;
				//System.out.println("Queue time: " + request.tQueue);
				//System.out.println("ReadHandler " + mcServerNo + "," + poolNo + " received request: " + new String(request.message));
				
				// send request to memcached server
				buffer.clear();
				buffer.put(request.message);
				buffer.flip();
				request.tServer = System.nanoTime();
				while (buffer.hasRemaining()) {
					client.write(buffer);
				}
				//System.out.println("ReadHandler sent the message to memcached");

				// block on read until we receive memcached response
				buffer.clear();
				int numRead = client.read(buffer);
				request.tServer = (System.nanoTime() - request.tServer)/1000;
				
				byte[] response = new byte[numRead];
			    System.arraycopy(buffer.array(), 0, response, 0, numRead);
			    String responseStr = new String(response);
				if (!responseStr.endsWith("END\r\n")) {
					request.fSuccess = 0;
				}
				//System.out.println("Memcached response: " + new String(response));
				
				// send memcached response to the client
				buffer.flip();
				while (buffer.hasRemaining()) {
					request.requestClient.write(buffer);
				}
				request.tMW = (System.nanoTime() - request.tMW)/1000;
				
				// sample log metrics
				if (count++%SAMPLINGRATE == 0) {
					String logMessage = String.format("%d, %d, %d, %d, %d, %d", request.fSuccess, request.tMW, request.tQueue, request.tServer, request.tHash, request.tWrite);
					MyMiddleware.myLogger.info(logMessage);
				}
			} catch (Exception e) {
				e.printStackTrace();
			}
		}
	}
	
}
