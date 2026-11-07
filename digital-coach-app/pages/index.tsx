import { apiFetch } from "@App/lib/auth/apiFetch";
import type { NextPage } from "next";
import { useState, useEffect } from "react";
import { useAuth } from "@App/lib/auth/AuthContextProvider";
import AuthGuard from "@App/lib/auth/AuthGuard";
import styles from "@App/styles/Home.module.scss";
import Card from "@App/components/atoms/Card";
//import IssuesChart from "@App/components/molecules/IssuesChart";
import dynamic from "next/dynamic";
import { TrendingUp, Award, Target, Video, History } from "lucide-react";
// import ScoreChart from "@App/components/molecules/ScoreChart";
//import PracticeCalendar from "@App/components/molecules/PracticeCalendar";
// import useGetFeaturedQuestionSets from "@App/lib/questionSets/useGetFeaturedQuestionSets";
import Link from "next/link";
// import useGetUserAverageScore from "@App/lib/interviewQuestion/useGetUserAverageScore";
// import useFetchUserInterviews from "@App/lib/interview/useFetchUserInterviews";
// import useGetAnswersByUserId from "@App/lib/answer/useGetAnswerByUserId";
// import seed from "@App/pages/api/seed";

const IssuesChart = dynamic(
  () => import("@App/components/molecules/IssuesChart"),
  {
    ssr: false,
    loading: () => <div>Loading chart...</div>,
  }
);

const Home: NextPage = () => {
  const { user, userData } = useAuth();

  // const {
  //   data: questionSets,
  //   isLoading,
  //   isFetching,
  // } = useGetFeaturedQuestionSets();
  // console.log(questionSets, isLoading, isFetching);

  // const {
  //   data: answerData,
  //   isLoading: isAnswerLoading,
  //   isFetching: isAnswerFetching,
  // } = useGetAnswersByUserId(user?.uid);

  // const {
  //   data: averageScore,
  //   isLoading: isLoadingAverageScore,
  //   isFetching: isFetchingAverageScore,
  // } = useGetUserAverageScore(user?.uid);

  const [tip, setTips] = useState("");
  const [heygenToken, setHeygenToken] = useState<string | null>(null);
  const [isCreatingSession, setIsCreatingSession] = useState(true);

  useEffect(() => {
    const tips = [
      "Practice active listening during the interview. Pay attention to the questions asked and respond thoughtfully.",
      "Research common behavioral interview questions and prepare STAR (Situation, Task, Action, Result) stories to showcase your skills and experiences.",
      "Arrive early for the interview to allow time for unexpected delays and to demonstrate your punctuality.",
      "Turn off your phone or set it to silent mode before the interview to avoid distractions.",
      "Maintain good body language throughout the interview. Sit up straight, make eye contact, and smile to convey confidence.",
      "Research the salary range for similar positions in your industry and be prepared to discuss salary expectations if asked.",
      "Practice good hygiene and grooming before the interview. A neat appearance contributes to a positive first impression.",
      "Review the job description and customize your answers to align with the requirements of the role.",
      "Stay positive and enthusiastic during the interview. A positive attitude can leave a lasting impression on the interviewer.",
      "Start by researching the company and your interviewer. Understanding key information about the company you’re interviewing with can help you go into your interview with confidence.",
      "Practice answering common interview questions to build your confidence and improve your responses during the actual interview.",
      "Dress appropriately for your interview. Your attire should be professional and suitable for the company culture.",
      "Prepare questions to ask the interviewer. This shows your interest in the position and company and can help you gather important information.",
      "Stay calm and composed during the interview. Take a deep breath if you feel nervous and focus on articulating your thoughts clearly.",
      "Highlight your achievements and relevant experiences during the interview. Use specific examples to demonstrate your skills and capabilities.",
      "Follow up with a thank-you email after the interview. Express your gratitude for the opportunity and reiterate your interest in the position.",
    ];
    const randInd = Math.floor(Math.random() * tips.length);
    setTips(tips[randInd]);
  }, []);

  useEffect(() => {
  async function preloadHeyGen() {
    try {
      setIsCreatingSession(true);

      const host = process.env.NEXT_PUBLIC_HOST;

if (!host) {
  throw new Error("NEXT_PUBLIC_HOST is not configured");
}

const response = await apiFetch(`${host}/api/heygen/session_token`);

      const token = await response.json();

      setHeygenToken(token);
    } catch (err) {
      console.error(err);
    } finally {
      setIsCreatingSession(false);
    }
  }

  preloadHeyGen();
}, []);
  // if (isLoading || isFetching) return <div>Loading...</div>;

  const mockIssuesData = [
    {
      skill: "No Eye Contact",
      value: 0.9,
    },
    {
      skill: "Filler Word",
      value: 0.75,
    },
    {
      skill: "Long Pause",
      value: 0.65,
    },
    {
      skill: "Voice Not Clear",
      value: 0.6,
    },
    {
      skill: "Off Topic",
      value: 0.4,
    },
  ];
  // const events =
  //   answerData?.docs.map((answer) => {
  //     return {
  //       start: answer.data().createdAt.toDate().toISOString(),
  //       end: answer.data().createdAt.toDate().toISOString(),
  //     };
  //   }) || [];

  return (
    <AuthGuard>
      <div className={styles.Home}>
        <header className={styles.header}>
          <div>
            <h1>Digital Coach</h1>
            <p>Welcome back, {userData?.name}!</p>
          </div>
        </header>

        <section className={styles.hero}>
          <div className={styles.heroContent}>
            <h2>Ready to ace your next interview?</h2>
            <p>
              Practice with our AI-powered interviewer and get instant feedback on your performance.
              Track your progress and improve your interview skills with personalized insights.
            </p>
            <div className={styles.heroActions}>
  {heygenToken ? (
    <Link
      href={{
        pathname: "/naturalconversation",
        query: {
          token: heygenToken,
        },
      }}
      className={styles.primaryCta}
    >
      <Video size={20} />
      <span>Start Mock Interview</span>
    </Link>
  ) : (
    <button disabled className={styles.primaryCta}>
      <Video size={20} />
      <span>Preparing Interview...</span>
    </button>
  )}

  <Link href="/progress" className={styles.secondaryCta}>
    <History size={20} />
    <span>View Interview History</span>
  </Link>
</div>
          </div>
        </section>

        <section className={styles.mainGrid}>
          <div className={styles.mainColumn}>
            
            <section className={styles.bottomGrid}>
              {/* Top Left Card */}
              <div className={styles.gridItem}>
                <Card title={"Most Common Flags"} multiline>
                  <div className={styles.issuesChartWrapper}>
                    <IssuesChart chartData={mockIssuesData} />
                  </div>
                </Card>
              </div>

              {/* Top Right Card */}
              <div className={styles.gridItem}>
                <Card title={"Your Random Interview Tip!"} multiline>
                  <div className={styles.tipoftheday}>
                    <p>{tip}</p>
                  </div>
                </Card>
              </div>

              {/* Bottom Full-Width Card */}
              <div className={styles.bottomFullWidth}>
                <Card title={"What You'll Get"} multiline>
                  <div className={styles.featuresContainer}>
                    {/* STAR Method Feature */}
                    <div className={styles.featureItem}>
                      <div className={`${styles.iconWrapper} ${styles.green}`}>
                        <Award size={20} />
                      </div>
                      <div className={styles.featureText}>
                        <h4>STAR Method Analysis</h4>
                        <p>
                          Get feedback on how well your answers follow the Situation,
                          Task, Action, Result framework
                        </p>
                      </div>
                    </div>

                    {/* Pacing Feedback Feature */}
                    <div className={styles.featureItem}>
                      <div className={`${styles.iconWrapper} ${styles.purple}`}>
                        <TrendingUp size={20} />
                      </div>
                      <div className={styles.featureText}>
                        <h4>Pacing Feedback</h4>
                        <p>
                          Learn if you&apos;re speaking too fast, too slow, or just
                          right for optimal communication
                        </p>
                      </div>
                    </div>

                    {/* Filler Word Feature */}
                    <div className={styles.featureItem}>
                      <div className={`${styles.iconWrapper} ${styles.orange}`}>
                        <Target size={20} />
                      </div>
                      <div className={styles.featureText}>
                        <h4>Filler Word Detection</h4>
                        <p>
                          Track usage of &quot;um&quot;, &quot;uh&quot;,
                          &quot;like&quot; and other filler words that can detract
                          from your message
                        </p>
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            </section>
            
          </div>
        </section>
      </div>
    </AuthGuard>
  );
};

export default Home;
