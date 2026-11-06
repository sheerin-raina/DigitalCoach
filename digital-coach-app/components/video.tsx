import { apiFetch } from "@App/lib/auth/apiFetch";
import React, { useRef, useState, useEffect } from "react";
// import styles from "@App/styles/NaturalConversationPage.module.scss";
import { Video, VideoOff, Mic, MicOff } from "lucide-react";
import styles from "@App/styles/interview/NaturalConversationPage.module.scss";
import { useAuth } from "@App/lib/auth/AuthContextProvider";
import { StreamingTranscriber } from "assemblyai";

export const MAX_SESSION_TIME = 1 * 300; // sandbox mode for HeyGen LiveAvatar only lasts for around 1 minute  
const MIN_SESSION_DURATION = 20; // minimum duration for an interview for it to be counted

// Define the shape of this components props
interface VideoRecorderProps {
    startInterview: () => Promise<void>;
    stopInterview: (duration: string, timeStarted: string) => Promise<void>;
    timeLeft: number; // timer
    setTimeLeft: React.Dispatch<React.SetStateAction<number>>; // pass in the setter for the parent's timeLeft state
    setCameraError: React.Dispatch<React.SetStateAction<string>>; // pass in the setter for the parent's cameraError state
onTranscriptChange?: (transcript: string, isFinal: boolean) => void; // optional callback for sending the transcript to the parent component
}

/**
 * Handles recording the user's camera and audio.
 */
function VideoRecorder({ startInterview, stopInterview, timeLeft, setTimeLeft, setCameraError, onTranscriptChange }: VideoRecorderProps) {
    const [isRecording, setIsRecording] = useState(false); // keep track of recording state
    const [stream, setStream] = useState<MediaStream>(); // stores user's camera stream
    const [videoURL, setVideoURL] = useState<string>(); // download URL for user's side of the interview
    const [videoEnabled, setVideoEnabled] = useState(false);
    const [audioEnabled, setAudioEnabled] = useState(false);

    const transcriberRef = useRef<StreamingTranscriber | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const workletNodeRef = useRef<AudioWorkletNode | null>(null);

    const videoRef = useRef<HTMLVideoElement>(null); // reference to video element 
    const mediaRecorderRef = useRef<MediaRecorder>(null); // reference to media recorder recording user's video/audio
    const streamRef = useRef<MediaStream>(null); // reference to user's video and/or audio streams
    const chunksRef = useRef<Blob[]>([]); // stores video as an array of chunks
    let isMounted = useRef(false);
    let timeStartedRef = useRef("");
    //const host = typeof window !== "undefined" ? "localhost:8000" : "api"; // if we're in the browser use localhost, but if we're in Docker, use the backend's service name (currently 'api')
    const host =
    typeof window !== "undefined"
        ? process.env.NEXT_PUBLIC_HOST
        : "api";

if (!host) {
  throw new Error("NEXT_PUBLIC_HOST is not configured");
}
    const { userData } = useAuth(); // extract user's Firestore data  

    const [pushToTalkMode, setPushToTalkMode] = useState(true);
    const [isTalking, setIsTalking] = useState(false);
    const isTalkingRef = useRef(false);
    const pushToTalkRef = useRef(true);


    const startTalking = () => {
        isTalkingRef.current = true;
        setIsTalking(true);
        console.log("Push-to-talk ON");
    };


    const stopTalking = () => {
        isTalkingRef.current = false;
        setIsTalking(false);
        console.log("Push-to-talk OFF");
    };
    const startingRef = useRef(false);

    // session terminates automatically when timer runs out
    useEffect(() => {
        let timer: NodeJS.Timeout;
        // decrement timer if interview is still going
        if (isRecording && timeLeft > 0) {
            // decrement every second
            timer = setInterval(() => {
                setTimeLeft((prevTime) => prevTime - 1);
            }, 1000);
        }
        // time is up, stop recording
        else if (isRecording && timeLeft === 0) {
            stopRecording();
        }

        // stop timer
        return () => clearInterval(timer);

    }, [isRecording, timeLeft]);

    useEffect(() => {
        startPreview();
        isMounted.current = true;

        return () => {
            // stop recording user camera and mic when component unmounts
            if (streamRef.current) {
                streamRef.current.getTracks().forEach((track) => track.stop());
                console.log("Turning off user camera and microphone...");
            }
            const stopAudio = async () => {

                // close websocket to AssemblyAI
                if (transcriberRef.current) {
                    await transcriberRef.current.close();
                    transcriberRef.current = null;
                }
                if (audioContextRef.current) {
                    await audioContextRef.current.close();
                    audioContextRef.current = null;
                }
            }
            stopAudio();
            isMounted.current = false;
        }
    }, []);

    useEffect(() => {
        const keyDown = (e: KeyboardEvent) => {
            if (e.code === "Space" && isRecording && pushToTalkMode) {
                startTalking();
            }
        };

        const keyUp = (e: KeyboardEvent) => {
            if (e.code === "Space") {
                stopTalking();
            }
        };

        window.addEventListener("keydown", keyDown);
        window.addEventListener("keyup", keyUp);

        return () => {
            window.removeEventListener("keydown", keyDown);
            window.removeEventListener("keyup", keyUp);
        };
    }, [isRecording]);

    /**
     * Toggles the user's video camera. Note that its pausing the camera recording and not completely turning it off so the video recording doesn't get disabled preemptively.
     */
    const toggleVideo = () => {
        const newState = !videoEnabled;
        setVideoEnabled(newState);
        // disable video track (this will not turn off the camera, but it will stop transmitting the camera feed from rendering, we need this so the entire video can be recorded)
        if (streamRef.current) {
            streamRef.current.getVideoTracks().forEach((track) => {
                track.enabled = newState;
            });
        }
    }

    /**
     * Toggles the user's microphone.
     */
    const toggleAudio = () => {
        const newState = !audioEnabled;
        setAudioEnabled(newState);
        if (streamRef.current) {
            streamRef.current.getAudioTracks().forEach((track) => {
                track.enabled = newState;
            });
        }
    }

    /**
     * Sets up the media recorder and starts recording user's camera and microphone.
     * @returns Video download URL
     */
   
    const startRecording = async () => {
    // Prevent double-starts
    if (startingRef.current || isRecording) {
        console.log("Recording/session already starting");
        return;
    }

    startingRef.current = true;

    try {
        // start preview in case media stream isn't set up yet
        if (!streamRef.current) {
            await startPreview();

            if (!streamRef.current) {
                throw new Error("Camera and microphone are not ready.");
            }
        }

        // create media recorder to record user's camera/audio
        const recordingStream = streamRef.current;

        if (!recordingStream) {
            throw new Error("Camera and microphone are not ready.");
        }

        const mediaRecorder = new MediaRecorder(recordingStream);
        mediaRecorderRef.current = mediaRecorder;
        chunksRef.current = []; // reset old data in chunks array

        // register event listener for when there's data available
        // add data to the chunks array
        mediaRecorder.ondataavailable = (event) => {
            if (event.data && event.data.size > 0) {
                chunksRef.current.push(event.data);
            }
        };

        // register event listener when recording stops
        // once the recorder stops, create download URL for user's side of the interview
        mediaRecorder.onstop = () => {
            const blob = new Blob(chunksRef.current, {
                type: "video/webm",
            });
            const url = URL.createObjectURL(blob);
            setVideoURL(url);
        };

        // save time when started
        timeStartedRef.current = new Date().toLocaleString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
        });

        setTimeLeft(MAX_SESSION_TIME);
        setVideoURL("");

        // get temporary AssemblyAI authentication token from our backend
        const response = await apiFetch(
            `${host}/api/assemblyai/token`,
            {
                method: "GET",
            }   
        );

        const { token } = await response.json();

        if (!response.ok) {
            throw new Error(
                response.statusText || "AssemblyAI token request failed"
            );
        }

        console.log("AssemblyAI token request successful!");

        // configurations for AssemblyAI API that get sent as query parameters to the WebSocket URL
        const transcriber = new StreamingTranscriber({
            token,
            sampleRate: 16000,
            speechModel: "universal-streaming-english",
            formatTurns: true,
            maxSpeakers: 2,
            speakerLabels: true,
        });

        // event handler for when connection to AssemblyAI API is established via websocket
        transcriber.on("open", ({ id }) => {
            console.log(
                `AssemblyAI ready to transcribe! Session id: ${id}`
            );
        });

        // event handler for when websocket to AssemblyAI is closed
        transcriber.on("close", (code: number, reason: string) => {
            console.log(
                `WebSocket closed: ${code}\nReason: ${reason}`
            );
        });

        // event handler for when we receive a message from AssemblyAI
        transcriber.on("turn", (message) => {
            if (message.end_of_turn && onTranscriptChange) {
                onTranscriptChange(
                    `${userData?.name || "User"}: ${message.transcript}`,
                    true
                );
            }
        });

        // event handler for when an error occurs
        transcriber.on("error", (error: Error) => {
            console.error(
                `AssemblyAI WebSocket Error: ${error}`
            );
        });

        await transcriber.connect();
        transcriberRef.current = transcriber;

        // create audio worklet to convert audio data into PCM data for AssemblyAI
        const audioContext = new window.AudioContext({
            sampleRate: 16000,
        });

        audioContextRef.current = audioContext;

        // create audio context source from user's video and audio stream
        const source =
            audioContext.createMediaStreamSource(recordingStream);

        // load audio worklet from Next.js public folder
        await audioContext.audioWorklet.addModule(
            "/pcmprocessor.js"
        );

        // instantiate the processor we registered as pcm-processor
        const workletNode = new AudioWorkletNode(
            audioContext,
            "pcm-processor"
        );

        workletNodeRef.current = workletNode;

        workletNode.port.onmessage = (event) => {
            if (
                transcriberRef.current &&
                (
                    !pushToTalkRef.current ||
                    isTalkingRef.current
                )
            ) {
                try {
                    transcriberRef.current.sendAudio(
                        event.data
                    );
                } catch (e) {
                    console.error(e);
                }
            }
        };

        // pipe the microphone data (source) into the audio worklet
        source.connect(workletNode);

        // IMPORTANT:
        // Mark recording BEFORE starting the interview
        setIsRecording(true);

        // Start camera recording
        mediaRecorder.start();

        // Start HeyGen session
        await startInterview();

    } catch (error) {
        console.error(
            `Error starting interview session:`,
            error
        );

        setIsRecording(false);
    } finally {
        startingRef.current = false;
    }
};

    /**
     * Stop recording user camera.
     */
    const stopRecording = async () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current?.stop(); // stop recording user camera and microphone

            // close websocket to AssemblyAI
            if (transcriberRef.current) {
                await transcriberRef.current.close();
                transcriberRef.current = null;
            }

            // release audio resources
            if (audioContextRef.current) {
                await audioContextRef.current.close();
                audioContextRef.current = null;
            }

            // turn of camera and microphone
            console.log("Turning off camera and mic...");
            if (streamRef.current) {
                streamRef.current.getTracks().forEach((track) => track.stop());
            }
            setIsRecording(false);

            // check if interview was too short to be counted
            const duration = MAX_SESSION_TIME - timeLeft;
            if (duration < MIN_SESSION_DURATION) {
                alert(`Interview must be at least ${MIN_SESSION_DURATION}s long to be counted.`);
                // restart interview
                window.location.href = "/naturalconversation";
                return;
            }

            // invoke callback from parent component (expected to stop HeyGen session and save interview)
            await stopInterview(formatDuration(duration), timeStartedRef.current);
        }
    }

    /**
     * Format duration into MMm SSs not 0-padded
     * @param seconds 
     */
    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60).toString();
        const secs = (seconds % 60).toString();
        return `${mins}m ${secs}s`;
    }

    /**
     * Requests user's video/audio and handles the preview of user's camera video.
     */
    const startPreview = async () => {
        try {
            // request access to user's camera and microphone
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: {
                    sampleRate: 16000, // AssemblyAI expects 16Hhz sample rate
                    channelCount: 1,
                    echoCancellation: true,
                    noiseSuppression: true,
                },
            });
            // if the user left webpage before giving permission, turn of camera and microphone
            if (!isMounted.current) {
                console.log("Component unmounted before camera loaded. Aborting...");
                mediaStream.getTracks().forEach((track) => track.stop());
                console.log("Turning off user camera and microphone...");
                return;
            }
            streamRef.current = mediaStream; // save media stream reference
            setStream(mediaStream); // store media stream
            // attach camera stream to video element to show live preview
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }

            // enable video and audio once user has agreed 
            setVideoEnabled(true);
            setAudioEnabled(true);

        } catch (error) {
            console.error(`Error accessing media device: ${error}`);
            if (error instanceof Error) {
                setCameraError(`${error.message}: Please allow video and audio permissions to proceed. You may disable them before recording begins.`);
                setVideoEnabled(false);
            }

        }
    }


    return (
        <>
            <div className={styles.videoCard}>
                <div className={`${styles.videoHeader} ${styles.userHeader}`}>
                    <p>Your Camera</p>
                    {/* Toggle video camera */}
                    <div className={styles.controls}>
                        <button
                            onClick={toggleVideo}
                            className={videoEnabled ? styles.enabled : styles.disabled}
                            disabled={!stream} // wait until video is ready before enabling toggling
                        >
                            {videoEnabled ? (
                                <Video />
                            ) : (
                                <VideoOff />
                            )}
                        </button>
                        {/* Toggle microphone */}
                        <button
                            onClick={toggleAudio}
                            className={audioEnabled ? styles.enabled : styles.disabled}
                            disabled={!stream} // wait until video is ready before enabling toggling
                        >
                            {audioEnabled ? (
                                <Mic />
                            ) : (
                                <MicOff />
                            )}
                        </button>
                    </div>
                </div>

                <div className={`${styles.videoContent} ${styles.userCamera}`}>
                    {/* User Camera Video */}
                    <video
                        ref={videoRef}
                        autoPlay
                        muted
                        style={{ display: videoEnabled ? "block" : "none" }}
                    />
                    {!videoEnabled && (
                        <div className={styles.cameraOff}>
                            <VideoOff />
                            <p>Camera is off</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Start/Stop Buttons */}
            <div className={styles.buttonBox}>

                {!isRecording ?
                    <button
                        className={`${styles.startButton} ${styles}`}
                        onClick={startRecording}
                        disabled={!stream}
                    >
                        Start Recording
                    </button> :
                    <>
                        <button
                            className={styles.startButton}
                            onClick={stopRecording}
                        >
                            Stop Recording
                        </button>

                        {pushToTalkMode && (
                            <button
                                className={styles.startButton}
                                onMouseDown={startTalking}
                                onMouseUp={stopTalking}
                                onMouseLeave={stopTalking}
                            >
                                {isTalking ? "🎤 Listening..." : "Hold to Talk"}
                            </button>
                        )}
                    </>
                }

                {/* If the video download URL is ready, store it in Firebase for preview later */}
                {/* {videoURL 
            ? <a href={videoURL} download="user-interview.webm" className={styles.startButton}>Download Video</a> : <a href=""></a>} */}
            </div>
        </>

    )
}

export default VideoRecorder;