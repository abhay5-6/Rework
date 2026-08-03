import { useState, useEffect, useRef, useCallback } from 'react';

// STUN servers for NAT traversal
const iceServers = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ]
};

type WebRTCSignalData = {
  sender_username: string;
  target_username?: string;
  offer?: RTCSessionDescriptionInit;
  answer?: RTCSessionDescriptionInit;
  candidate?: RTCIceCandidateInit;
};

type WebRTCSignalMessage = {
  type: string;
  data: WebRTCSignalData;
};

/**
 * Custom React Hook for WebRTC Mesh Peer-to-Peer Video/Audio Calling.
 * Handles local camera/mic stream capture, ICE candidate exchange, SDP offer/answer signaling over WebSocket,
 * and remote peer stream tracking.
 */
export function useWebRTC(roomId: number, currentUser: string, socketRef: React.MutableRefObject<WebSocket | null>) {
  void roomId;
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const [remoteStreams, setRemoteStreams] = useState<{ [username: string]: MediaStream }>({});
  const [inCall, setInCall] = useState(false);
  const inCallRef = useRef(false);
  
  const peerConnections = useRef<{ [username: string]: RTCPeerConnection }>({});
  const iceCandidatesQueue = useRef<{ [username: string]: RTCIceCandidateInit[] }>({});
  const isProcessingRef = useRef(false);
  const messageQueue = useRef<WebRTCSignalMessage[]>([]);

  const startCall = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setLocalStream(stream);
      localStreamRef.current = stream;
      setInCall(true);
      inCallRef.current = true;
      
      // Announce to the workspace that we joined
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        console.log("Sending join_call");
        socketRef.current.send(JSON.stringify({
          type: "join_call",
          data: {}
        }));
      }
    } catch (err) {
      console.error("Failed to get local stream", err);
      alert("Could not access camera/microphone");
    }
  }, [socketRef]);

  const leaveCall = useCallback(() => {
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
    }
    setLocalStream(null);
    localStreamRef.current = null;
    setRemoteStreams({});
    setInCall(false);
    inCallRef.current = false;
    
    // Close all peer connections
    Object.values(peerConnections.current).forEach(pc => pc.close());
    peerConnections.current = {};

    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: "leave_call",
        data: {}
      }));
    }
  }, [socketRef]);

  const createPeerConnection = useCallback((targetUsername: string, isInitiator: boolean) => {
    if (peerConnections.current[targetUsername]) {
      return peerConnections.current[targetUsername];
    }

    const pc = new RTCPeerConnection(iceServers);
    peerConnections.current[targetUsername] = pc;

    // Add local tracks
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => {
        pc.addTrack(track, localStreamRef.current!);
      });
    }

    // Handle ICE candidates
    pc.onicecandidate = (event) => {
      if (event.candidate && socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify({
          type: "webrtc_ice_candidate",
          data: {
            target_username: targetUsername,
            candidate: event.candidate
          }
        }));
      }
    };

    // Handle remote tracks
    pc.ontrack = (event) => {
      const stream = event.streams && event.streams.length > 0 
        ? event.streams[0] 
        : new MediaStream([event.track]);
        
      setRemoteStreams(prev => ({
        ...prev,
        [targetUsername]: stream
      }));
    };

    pc.oniceconnectionstatechange = () => {
      console.log(`ICE Connection State [${targetUsername}]:`, pc.iceConnectionState);
    };

    pc.onconnectionstatechange = () => {
      console.log(`Connection State [${targetUsername}]:`, pc.connectionState);
      // Removed leaveCall() here to prevent it from tearing down the call for temporary failures
    };

    if (isInitiator) {
      pc.createOffer()
        .then(offer => {
          if (socketRef.current?.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({
              type: "webrtc_offer",
              data: {
                target_username: targetUsername,
                offer: offer
              }
            }));
          }
          return pc.setLocalDescription(offer);
        })
        .catch(console.error);
    }

    return pc;
  }, [socketRef]);

  const processMessageQueue = useCallback(async () => {
    if (isProcessingRef.current || messageQueue.current.length === 0) return;
    isProcessingRef.current = true;

    try {
      while (messageQueue.current.length > 0) {
        const msg = messageQueue.current.shift();
        if (!msg) continue;
        
        const { type, data } = msg;
        const sender = data.sender_username;
        const target = data.target_username;

        if (sender === currentUser) continue;

        switch (type) {
          case "join_call":
            console.log(`Received join_call from ${sender}`);
            // Someone joined, we should initiate a connection to them
            createPeerConnection(sender, true);
            break;

          case "leave_call":
            console.log(`Received leave_call from ${sender}`);
            if (peerConnections.current[sender]) {
              peerConnections.current[sender].close();
              delete peerConnections.current[sender];
              setRemoteStreams(prev => {
                const next = { ...prev };
                delete next[sender];
                return next;
              });
            }
            break;

          case "webrtc_offer":
            if (target !== currentUser) return;
            if (!data.offer) return;
            console.log(`Received webrtc_offer from ${sender}`);
            const pcOffer = createPeerConnection(sender, false);
            await pcOffer.setRemoteDescription(new RTCSessionDescription(data.offer));
            
            if (iceCandidatesQueue.current[sender]) {
              for (const candidate of iceCandidatesQueue.current[sender]) {
                try {
                  await pcOffer.addIceCandidate(new RTCIceCandidate(candidate));
                } catch {
                  // Ignore stale candidates; another candidate may still connect.
                }
              }
              iceCandidatesQueue.current[sender] = [];
            }

            const answer = await pcOffer.createAnswer();
            
            if (socketRef.current?.readyState === WebSocket.OPEN) {
              socketRef.current.send(JSON.stringify({
                type: "webrtc_answer",
                data: {
                  target_username: sender,
                  answer: answer
                }
              }));
            }
            await pcOffer.setLocalDescription(answer);
            break;

          case "webrtc_answer":
            if (target !== currentUser) return;
            if (!data.answer) return;
            console.log(`Received webrtc_answer from ${sender}`);
            const pcAnswer = peerConnections.current[sender];
            if (pcAnswer) {
              await pcAnswer.setRemoteDescription(new RTCSessionDescription(data.answer));
              
              if (iceCandidatesQueue.current[sender]) {
                for (const candidate of iceCandidatesQueue.current[sender]) {
                  try {
                    await pcAnswer.addIceCandidate(new RTCIceCandidate(candidate));
                  } catch {
                    // Ignore stale candidates; another candidate may still connect.
                  }
                }
                iceCandidatesQueue.current[sender] = [];
              }
            }
            break;

          case "webrtc_ice_candidate":
            if (target !== currentUser) return;
            if (!data.candidate) return;
            const pcIce = peerConnections.current[sender];
            if (pcIce && pcIce.remoteDescription) {
              try {
                await pcIce.addIceCandidate(new RTCIceCandidate(data.candidate));
              } catch (e) {
                console.error("Error adding ice candidate", e);
              }
            } else {
              if (!iceCandidatesQueue.current[sender]) {
                iceCandidatesQueue.current[sender] = [];
              }
              iceCandidatesQueue.current[sender].push(data.candidate);
            }
            break;
        }
      }
    } finally {
      isProcessingRef.current = false;
      if (messageQueue.current.length > 0) {
        processMessageQueue();
      }
    }
  }, [currentUser, createPeerConnection, socketRef]);

  const handleSignalingData = useCallback((msg: WebRTCSignalMessage) => {
    if (!inCallRef.current) return;
    messageQueue.current.push(msg);
    processMessageQueue();
  }, [processMessageQueue]);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      leaveCall();
    };
  }, [leaveCall]);

  return {
    localStream,
    remoteStreams,
    inCall,
    startCall,
    leaveCall,
    handleSignalingData
  };
}
