package ch.ethz.gtouloup;

import java.nio.ByteBuffer;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.List;
import java.util.SortedMap;
import java.util.TreeMap;

public class ConsistentHash {
	private final int virtualNodesNo;
	private final SortedMap<Integer, Integer> circle = new TreeMap<Integer, Integer>();

	public ConsistentHash(int virtualNodesNo, List<String> mcAddresses) {
		this.virtualNodesNo = virtualNodesNo;

		for (int i = 0; i < mcAddresses.size(); i++) {
			add(mcAddresses.get(i), i);
		}
	}

	public void add(String mcAddress, int mcServerNo) {
		for (int i = 0; i < virtualNodesNo; i++) {
			circle.put(hashFunction((mcAddress + i).getBytes()), mcServerNo);
		}
	}

	public void remove(String mcAddress) {
		for (int i = 0; i < virtualNodesNo; i++) {
			circle.remove(hashFunction((mcAddress + i).getBytes()));
		}
	}

	public int get(byte[] key) {
		if (circle.isEmpty()) {
			return -1;
		}
		int hash = hashFunction(key);
		if (!circle.containsKey(hash)) {
			SortedMap<Integer, Integer> tailMap = circle.tailMap(hash);
			if (tailMap.isEmpty()) {
				hash = circle.firstKey();
			}
			else {
				hash = tailMap.firstKey();
			}
		}
		return circle.get(hash);
	}

	private int hashFunction(byte[] key) {
		MessageDigest md;
		try {
			md = MessageDigest.getInstance("MD5");
			byte[] digest = md.digest(key);
			int digestInt = ByteBuffer.wrap(digest).getInt();
			//System.out.println("digestInt: " + digestInt);
			
			return digestInt;
		} catch (NoSuchAlgorithmException e) {
			e.printStackTrace();
			return -1;
		}

	}
	
}
