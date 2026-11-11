import { useRouter } from "next/router";
import { useState, useEffect } from "react";
import styles from "@App/styles/interview/Results.module.scss";
import { doc, getDoc } from "firebase/firestore";
import { db } from "@App/lib/firebase/firebase.config";
import { useAuth } from "@App/lib/auth/AuthContextProvider";
import { IInterview } from "@App/lib/interview/models"
import { Calendar, Clock, Star, BookOpenText, Crown, Heart, CirclePlus } from "lucide-react";

/**
 * Webpage for a specific interview. 
 * @returns Webpage that displays the interview-related results
 */
export default function InterviewResults() {
    const router = useRouter();
    const [interview, setInterview] = useState<IInterview>();
    const { user, loading: authLoading } = useAuth();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!router.isReady || authLoading) return;
        let cancelled = false;
        const loadInterview = async () => {
            setLoading(true);
            setError("");
            setInterview(undefined);
            try {
                if (!user) throw new Error("Please sign in to view your interview.");
                const id = router.query.id;
                if (typeof id !== "string") throw new Error("Invalid interview ID.");
                const snapshot = await getDoc(doc(db, "users", user.uid, "interviews", id));
                if (!snapshot.exists()) throw new Error("Interview not found.");
                if (!cancelled) setInterview({ ...snapshot.data(), id: snapshot.id } as IInterview);
            } catch (err) {
                if (!cancelled) setError(err instanceof Error ? err.message : "Unable to load interview.");
            } finally {
                if (!cancelled) setLoading(false);
            }
        };
        void loadInterview();
        return () => { cancelled = true; };
    }, [router.isReady, router.query.id, user, authLoading]);

    if (loading) return <p role="status">Loading interview...</p>;
    if (error) return <p role="alert">{error}</p>;

    return (
        <div className={styles.performanceResults}>
            <div className={styles.resultsContainer}>
                {/* Overall Score */}
                <div className={styles.overallScore}>
                    <h1>Interview Performance</h1>
                    <div className={styles.scoreDisplay}>
                        <div className={styles.scoreValue}>
                            {interview?.metrics?.overall_score ?? "Not available"}
                        </div>
                        <p className={styles.scoreLabel}>Overall Score</p>
                    </div>
                    <div className={styles.metadata}>
                        <div className={styles.metadataItem}>
                            <Calendar/>
                            <span>{interview?.date}</span>
                        </div>
                        <div className={styles.metadataItem}>
                            <Clock/>
                            <span>{interview?.duration}</span>
                        </div>
                    </div>
                </div>
        
                {/* Performance Metrics */}
                <div className={styles.metricsGrid}>
                    {/* STAR Method */}
                    <div className={styles.metricCard}>
                        <div className={styles.metricHeader}>
                            <div className={styles.metricIcon}>
                                <Star/>
                            </div>
                            <div className={styles.metricInfo}>
                                <h3>STAR Method</h3>
                                <p>Structure Quality</p>
                            </div>
                        </div>

                        <div className={styles.scoreBadge}>
                            <span className={styles.scoreText}>
                                {interview?.feedback?.overall_competency?.star?.score ?? "Not available"}
                            </span>
                        </div>
                        <p className={styles.feedbackText}>{interview?.feedback?.overall_competency?.star?.summary ?? "Feedback has not been generated."}</p>
                    </div>

                    {/* Pacing Score */}
                    <div className={styles.metricCard}>
                        <div className={styles.metricHeader}>
                            <div className={styles.metricIcon}>
                                <BookOpenText/>
                            </div>
                            <div className={styles.metricInfo}>
                                <h3>Clarity</h3>
                                <p>Speech Rate</p>
                            </div>
                        </div>

                        <div className={styles.scoreBadge}>
                            <span className={styles.scoreText}>
                                {interview?.feedback?.overall_competency?.clarity?.score ?? "Not available"}
                            </span>
                        </div>
                        <p className={styles.feedbackText}>
                            {interview?.feedback?.overall_competency?.clarity?.summary ?? "Feedback has not been generated."}
                        </p>
                    </div>

                    {/* Filler Words */}
                    <div className={styles.metricCard}>
                        <div className={styles.metricHeader}>
                            <div className={styles.metricIcon}>
                                <Crown/>
                            </div>
                            <div className={styles.metricInfo}>
                                <h3>Confidence</h3>
                                <p>Filler/Hedge Words</p>
                            </div>
                        </div>
                        <div className={styles.scoreBadge}>
                            <div className={styles.scoreText}>{interview?.feedback?.overall_competency?.confidence?.score ?? "Not available"}
                            </div>
                        </div>
                        <p className={styles.feedbackText}>
                            {interview?.feedback?.overall_competency?.confidence?.summary ?? "Feedback has not been generated."}
                        </p>
                    </div>

                    {/* Sentiment/Engagement */}
                    <div className={styles.metricCard}>
                        <div className={styles.metricHeader}>
                            <div className={styles.metricIcon}>
                                <Heart/>
                            </div>
                            <div className={styles.metricInfo}>
                                <h3>Engagement</h3>
                                <p>Emotional Tone</p>
                            </div>
                        </div>
                        <div className={styles.scoreBadge}>
                            <div className={styles.scoreText}>
                                {interview?.feedback?.overall_competency?.engagement?.score ?? "Not available"}
                            </div>
                        </div>
                        <p className={styles.feedbackText}>
                            {interview?.feedback?.overall_competency?.engagement?.summary ?? "Feedback has not been generated."}
                        </p>
                    </div>
                </div>

                <section>
                    <h2>Transcript</h2>
                    <p style={{ whiteSpace: "pre-wrap" }}>{Array.isArray(interview?.transcript) ? interview.transcript.join("\n") : interview?.transcript || "No transcript was recorded."}</p>
                    <h2>Sentiment analysis</h2>
                    <p>{interview?.sentiment ? "Analysis saved." : "Analysis is pending or could not be completed."}</p>
                    {interview?.sentiment && <pre style={{ whiteSpace: "pre-wrap" }}>{typeof interview.sentiment === "string" ? interview.sentiment : JSON.stringify(interview.sentiment, null, 2)}</pre>}
                </section>

                {/* Action Buttons */}
                <div className={styles.actionButtons}>
                    <button
                        onClick={() => router.push("/naturalconversation")}
                        className={styles.practiceButton}
                    >
                      Practice Again  
                    </button>
                    <button
                        onClick={() => router.push("/progress")}
                        className={styles.viewHistory}>
                        View All Interviews
                    </button>
                </div>
            </div>    
        </div>
    )
}