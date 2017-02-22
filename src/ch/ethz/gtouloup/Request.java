package ch.ethz.gtouloup;

import java.nio.channels.SocketChannel;
import java.util.ArrayList;
import java.util.List;

public class Request {
	
	public SocketChannel requestClient;
	public byte[] message;
	public List<byte[]> responses = new ArrayList<>();
	public long tMW = 0;
	public long tQueue = 0;
	public long tServer = 0;
	public long tHash = 0;
	public long tWrite = 0;
	public int fSuccess = 1;
	
	public Request(SocketChannel requestClient, byte[] message) {
		this.requestClient = requestClient;
		this.message = message;
	}
	
}
