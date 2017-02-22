package ch.ethz.gtouloup;

import java.io.IOException;
import java.io.UnsupportedEncodingException;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.channels.SelectionKey;
import java.nio.channels.Selector;
import java.nio.channels.ServerSocketChannel;
import java.nio.channels.SocketChannel;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.Iterator;
import java.util.List;
import java.util.concurrent.LinkedBlockingQueue;

public class NIOServer extends Thread {

	private Selector selector;
	private ServerSocketChannel serverSocketChannel;
	private final int BUFFERSIZE = 2048;
	private ByteBuffer buffer = ByteBuffer.allocate(BUFFERSIZE);
	
	private ConsistentHash consistentHash;
	private List<LinkedBlockingQueue<Request>> writeQueues;
	private List<LinkedBlockingQueue<Request>> readQueues;
	private List<WriteHandler> writeHandlers;
	
	public NIOServer(String myIp, int myPort, ConsistentHash consistentHash, List<LinkedBlockingQueue<Request>> writeQueues,
			List<LinkedBlockingQueue<Request>> readQueues, List<WriteHandler> writeHandlers) {
		this.consistentHash = consistentHash;
		this.writeQueues = writeQueues;
		this.readQueues = readQueues;
		this.writeHandlers = writeHandlers;		
	    try {
			selector = Selector.open();
			serverSocketChannel = ServerSocketChannel.open();
			InetSocketAddress myAddress = new InetSocketAddress(myIp, myPort);
			serverSocketChannel.bind(myAddress);		
			serverSocketChannel.configureBlocking(false);
			serverSocketChannel.register(selector, SelectionKey.OP_ACCEPT);
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	public void run() {
		while (true) {
			try {
				selector.select();
				long tRequest = System.nanoTime();
				Iterator<SelectionKey> selectedKeys = selector.selectedKeys().iterator();
				
				while (selectedKeys.hasNext()) {
					SelectionKey key = selectedKeys.next();
					selectedKeys.remove();
					
					if (key.isAcceptable()) {
						accept(key);
					} 
					else if (key.isReadable()) {
						read(key, tRequest);
					}
				}
			} catch (Exception e) {
				e.printStackTrace();
			}
		}
	}
	
	private void accept(SelectionKey key) throws IOException {
		ServerSocketChannel serverSocketChannel = (ServerSocketChannel) key.channel();
		SocketChannel socketChannel = serverSocketChannel.accept();
		socketChannel.configureBlocking(false);
		socketChannel.register(selector, SelectionKey.OP_READ);
	}
	
	private void read(SelectionKey key, long tRequest) throws IOException, NoSuchAlgorithmException, InterruptedException {
		long tHash = System.nanoTime();
		SocketChannel socketChannel = (SocketChannel) key.channel();
		buffer.clear();
		int numRead;
	    try {
	    	numRead = socketChannel.read(buffer);
	    } 
	    catch (IOException e) {
	    	// the remote forcibly closed the connection
	    	socketChannel.close();
	    	key.cancel();
	    	return;
	    }
	    if (numRead == -1) {
	    	// the remote shut the socket down cleanly
	    	socketChannel.close();
		    key.cancel();
		    return;
	    }
	    
	    byte[] message = new byte[numRead];
	    System.arraycopy(buffer.array(), 0, message, 0, numRead);
		//int mcServerNo = getServerNo(message);
	    // ISO-8859-1 allows for 1-1 mapping between bytes and characters
		String messageStr = new String(message, "ISO-8859-1");
		byte[] messageKey = messageStr.split(" ")[1].trim().getBytes("ISO-8859-1");
		int mcServerNo = MyMiddleware.consistentHash.get(messageKey);

		//String messageStr = new String(message);
		//System.out.println("-----------------");
		//System.out.println("Message received: " + messageStr);
		//System.out.println("MessageKey: " + messageStr.split(" ")[1].trim());
		//System.out.println("Memcache server No: " + mcServerNo);
		
		Request request = new Request(socketChannel, message);
		request.tMW = tRequest;
		decode(request, mcServerNo);
		request.tHash = (System.nanoTime() - tHash)/1000;
		//handle very small values
		if (request.tHash > 100000) {
			request.tHash = 0;
		}
	}
	
	private void decode(Request request, int mcServerNo) throws InterruptedException{
		String op = new String(request.message).split(" ")[0].toLowerCase();
		if ((op.equals("set")) || (op.equals("delete"))) {
			request.tQueue = System.nanoTime();
			writeQueues.get(mcServerNo).put(request);
			writeHandlers.get(mcServerNo).notifyWriteHandler();
			//System.out.println("Request enqueued in " + mcServerNo + "writeQueue: " + new String(request.message));
		}
		else if (op.equals("get")) {
			request.tQueue = System.nanoTime();
			readQueues.get(mcServerNo).put(request);
			//System.out.println("Request enqueued in " + mcServerNo + "readQueue: " + new String(request.message));
		}
	}
	
}
