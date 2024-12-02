from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain_community.chat_models import ChatOllama
from langchain.prompts import PromptTemplate
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Optional
import re
import json


class YouTubeSummarizer:
    def __init__(self):
        """
        Initialize the YouTube Summarizer
        """

        self.llm = ChatOllama(temperature=0, model="llama3.2")

        # Initialize text splitter for long transcripts
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000, chunk_overlap=1000, separators=["\n\n", "\n", " ", ""]
        )

        # Custom prompts for the summary chain
        self.map_prompt_template = """Extract the key information from this transcript section:
{text}

Return a brief summary focusing on the main points discussed."""

        self.combine_prompt_template = """Create a structured summary of the video content from these summaries. 
Format your response as a JSON object with the following structure:
{{
    "main_topic": "Brief one-sentence description of the video's main topic",
    "key_points": [
        "First key point",
        "Second key point",
        "Third key point"
    ],
    "important_details": [
        "First important detail",
        "Second important detail",
        "Third important detail"
    ],
    "takeaways": [
        "First main takeaway",
        "Second main takeaway",
        "Third main takeaway"
    ]
}}

Summaries to combine:
{text}

Remember to maintain valid JSON format and include all required fields."""

        # Create the summary chain
        self.map_prompt = PromptTemplate(
            template=self.map_prompt_template, input_variables=["text"]
        )

        self.combine_prompt = PromptTemplate(
            template=self.combine_prompt_template, input_variables=["text"]
        )

        self.chain = load_summarize_chain(
            llm=self.llm,
            chain_type="map_reduce",
            map_prompt=self.map_prompt,
            combine_prompt=self.combine_prompt,
            verbose=True,
            return_intermediate_steps=True,
        )

    def extract_video_id(self, youtube_url: str) -> Optional[str]:
        """
        Extract video ID from various forms of YouTube URLs

        Args:
            youtube_url (str): YouTube video URL

        Returns:
            str: Video ID if found, None otherwise
        """
        patterns = [
            r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?]*)",
            r"(?:youtube\.com\/shorts\/)([^&\n?]*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        return None

    def get_transcript(self, video_id: str) -> str:
        """
        Get the transcript of a YouTube video

        Args:
            video_id (str): YouTube video ID

        Returns:
            str: Combined transcript text
        """
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry["text"] for entry in transcript_list])
        except Exception as e:
            raise Exception(f"Error getting transcript: {str(e)}")

    def summarize_video(self, youtube_url: str) -> dict:
        try:
            video_id = self.extract_video_id(youtube_url)
            if not video_id:
                return {"status": "error", "message": "Invalid YouTube URL"}

            transcript = self.get_transcript(video_id)
            texts = self.text_splitter.create_documents([transcript])

            try:
                # chain.invoke()를 사용하여 명시적으로 출력 키 지정
                result = self.chain.invoke({"input_documents": texts})

                print("Chain result:", result)  # 디버깅용 출력

                # 'output_text' 키에서 요약 추출
                if isinstance(result, dict) and "output_text" in result:
                    raw_summary = result["output_text"]
                else:
                    return {"status": "error", "message": "Unexpected result format"}

                # JSON 파싱 시도
                try:
                    # JSON 부분 추출
                    start_idx = raw_summary.find("{")
                    end_idx = raw_summary.rfind("}")

                    if start_idx == -1 or end_idx == -1:
                        return {
                            "status": "error",
                            "message": "No valid JSON found in response",
                        }

                    json_str = raw_summary[start_idx : end_idx + 1]
                    json_str = json_str.replace("\n", " ").replace("    ", " ").strip()

                    structured_summary = json.loads(json_str)

                    # 필수 필드 확인
                    required_fields = [
                        "main_topic",
                        "key_points",
                        "important_details",
                        "takeaways",
                    ]
                    for field in required_fields:
                        if field not in structured_summary:
                            structured_summary[field] = []
                        elif field != "main_topic" and not isinstance(
                            structured_summary[field], list
                        ):
                            structured_summary[field] = [structured_summary[field]]

                    return {
                        "status": "success",
                        "summary": structured_summary,
                        "video_id": video_id,
                    }

                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {str(e)}")
                    print(f"Attempted to parse: {json_str}")
                    return {
                        "status": "error",
                        "message": f"Failed to parse summary: {str(e)}",
                    }

            except Exception as e:
                print(f"Chain execution error: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Chain execution failed: {str(e)}",
                }

        except Exception as e:
            print(f"General error: {str(e)}")
            return {"status": "error", "message": str(e)}
