import asyncio
from datetime import date, datetime as dt  # Aliased datetime
from typing import List, Optional, Dict, Any, Union

import pytz  # For timezone handling
from google.oauth2.credentials import Credentials
from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext, Tool  # Added RunContext and Tool
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart

from pkg.llm.prompts import get_calendar_bot_system_prompt
from pkg.log.logger import Logger
from pkg.llm.client import LLMModel, gemini_model_map
from integration_clients.g_suite.client import GSuiteClient
from integration_clients.g_suite.types import TimeSlot, Appointment as GSuiteAppointment


class Deps(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    g_credentials: Credentials
    g_suite_client: GSuiteClient


# Tool Input Models
class CheckAvailabilityArgs(BaseModel):
    start_date: date = Field(
        ...,
        description=f"The start date for checking availability, in YYYY-MM-DD format. Infer from conversation. Today is {dt.now().strftime('%Y-%m-%d')}."
    )
    end_date: date = Field(
        ...,
        description="The end date for checking availability, in YYYY-MM-DD format. Infer from conversation. Often 2-3 days from start_date if not specified by user."
    )
    duration_minutes: int = Field(
        default=30,
        description="The duration of the meeting in minutes. Defaults to 30 minutes."
    )
    user_timezone: str = Field(
        default='UTC',
        description="The user's timezone to correctly interpret dates and define business hours (e.g., 'America/New_York'). Defaults to UTC."
    )
    business_hour_start: int = Field(
        default=9,
        description="Business day start hour (e.g., 9 for 9 AM in user_timezone)."
    )
    business_hour_end: int = Field(
        default=18,
        description="Business day end hour (e.g., 18 for 6 PM in user_timezone)."
    )
    calendar_id: str = Field(
        default='primary',
        description="Calendar ID to check. Defaults to 'primary'."
    )


class CreateAppointmentArgs(BaseModel):
    title: str = Field(..., description="The title of the appointment.")
    start_time: dt = Field(
        ...,
        description="The start date and time of the appointment in 'YYYY-MM-DD HH:MM:SS' format. This MUST be in UTC."
    )
    end_time: dt = Field(
        ...,
        description="The end date and time of the appointment in 'YYYY-MM-DD HH:MM:SS' format. This MUST be in UTC."
    )
    description: Optional[str] = Field(
        None,
        description="A description for the appointment."
    )
    attendees: List[str] = Field(
        default_factory=list,
        description="A list of attendee email addresses."
    )
    location: Optional[str] = Field(
        None,
        description="The location of the appointment."
    )
    calendar_id: str = Field(
        default='primary',
        description="Calendar ID to create the event in. Defaults to 'primary'."
    )
    send_notifications: bool = Field(
        default=True,
        description="Whether to send notifications to attendees. Defaults to true."
    )


class CalendarAgent:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.system_prompt = get_calendar_bot_system_prompt(calendar_linked=True)

        # Ensure the model name from gemini_model_map is compatible with Pydantic-AI's GeminiModel or direct string usage
        model_name_str = gemini_model_map.get(LLMModel.GEMINI_2_5_FLASH.value)
        if not model_name_str:
            raise ValueError("Gemini model name not found in map for GEMINI_2_5_FLASH")

        # The Pydantic-AI examples often use model name string directly, e.g. "gemini-pro"
        # Depending on how GeminiModel is implemented/used by pydantic-ai, this might need adjustment.
        # Assuming GeminiModel takes the string name and handles provider details.
        model_value = GeminiModel(model_name=model_name_str)
        # If "provider" is required by your GeminiModel setup:
        # model_value = GeminiModel(model_name=model_name_str, provider="google-gla")

        agent = Agent(
            model=model_value,
            system_prompt=self.system_prompt,
        )

        @agent.tool
        async def CheckCalendarAvailability( ctx: RunContext[Deps], args: CheckAvailabilityArgs) -> List[
                                                                                                             TimeSlot] | str:
            self.logger.info(f"Tool: CheckCalendarAvailability called with args: {args}")
            try:
                g_suite_client = ctx.deps.g_suite_client
                g_credentials = ctx.deps.g_credentials

                available_slots = await g_suite_client.get_available_slots(
                    credentials=g_credentials,
                    start_date=args.start_date,
                    end_date=args.end_date,
                    duration_minutes=args.duration_minutes,
                    calendar_id=args.calendar_id,
                    timezone=args.user_timezone,  # For business hours calculation
                    business_hour_start=args.business_hour_start,
                    business_hour_end=args.business_hour_end
                )
                if not available_slots:
                    return "No available slots found for the specified criteria. You might want to suggest trying different dates or a wider range."
                return available_slots
            except Exception as e:
                self.logger.error(f"Error in CheckCalendarAvailability tool: {e!s}")
                return f"An error occurred while checking calendar availability: {e!s}. Please inform the user."

        @agent.tool
        async def CreateCalendarAppointment(ctx: RunContext[Deps], args: CreateAppointmentArgs) -> Dict[
                                                                                                             str, Any] | str:
            self.logger.info(f"Tool: CreateCalendarAppointment called with args: {args}")
            try:
                g_suite_client = ctx.deps.g_suite_client
                g_credentials = ctx.deps.g_credentials

                # GSuiteClient.create_event expects an object with specific attributes.
                # Create a temporary object that duck-types the parts of GSuiteAppointment needed.
                class MinimalAppointmentForCreation:
                    def __init__(self, title, description, start_time, end_time, attendees, location):
                        self.title = title
                        self.description = description
                        self.start_time = start_time  # datetime object
                        self.end_time = end_time  # datetime object
                        self.attendees = attendees
                        self.location = location

                appointment_data = MinimalAppointmentForCreation(
                    title=args.title,
                    description=args.description,
                    start_time=args.start_time.replace(
                        tzinfo=pytz.UTC) if args.start_time.tzinfo is None else args.start_time,
                    end_time=args.end_time.replace(tzinfo=pytz.UTC) if args.end_time.tzinfo is None else args.end_time,
                    attendees=args.attendees,
                    location=args.location
                )

                created_event = await g_suite_client.create_event(
                    credentials=g_credentials,
                    appointment=appointment_data,  # Pass the ad-hoc object
                    calendar_id=args.calendar_id,
                    send_notifications=args.send_notifications
                )
                self.logger.info(f"Event created successfully: {created_event.get('id')}")
                return {"status": "success", "event_summary": created_event.get('summary'),
                        "event_id": created_event.get('id'), "html_link": created_event.get('htmlLink')}
            except Exception as e:
                self.logger.error(f"Error in CreateCalendarAppointment tool: {e!s}")
                # Provide a user-friendly error message if possible, or a generic one.
                return f"An error occurred while creating the appointment: {e!s}. Please inform the user and perhaps suggest they try again after checking their inputs."

        self.agent = agent

    async def run(self, prompt_text: str, history: List[Dict[str, str]], deps: Deps) -> str:
        self.logger.info(f"Calendar Agent received prompt: '{prompt_text}'")

        # Convert history to proper pydantic-ai message format
        formatted_history: List[Union[ModelRequest, ModelResponse]] = []
        
        for msg_dict in history:
            role_str = msg_dict.get("role")
            content_str = msg_dict.get("content")
            
            if not content_str:
                self.logger.warning(f"Skipping history message with missing content: role='{role_str}'")
                continue
                
            if role_str == "user":
                # Create ModelRequest with UserPromptPart
                user_request = ModelRequest(parts=[UserPromptPart(content=content_str)])
                formatted_history.append(user_request)
            elif role_str == "assistant":
                # Create ModelResponse with TextPart
                assistant_response = ModelResponse(parts=[TextPart(content=content_str)])
                formatted_history.append(assistant_response)
            else:
                self.logger.warning(f"Skipping history message with invalid role: role='{role_str}'")

        try:
            agent_run_response = await self.agent.run(user_prompt=prompt_text,
                message_history=formatted_history if formatted_history else None,
                deps=deps
            )

            # Extract the textual response from the agent's execution
            # (AgentRun object from pydantic-ai)
            if hasattr(agent_run_response, 'output') and \
                    agent_run_response.output:
                response_content = agent_run_response.output
                if response_content:
                    return str(response_content)

            # Fallback if latest_message is not directly usable or empty
            if hasattr(agent_run_response, 'messages') and agent_run_response.messages:
                for msg in reversed(agent_run_response.messages):
                    if hasattr(msg, 'parts') and msg.parts:
                        for part in msg.parts:
                            if hasattr(part, 'content') and part.content:
                                return str(part.content)

            self.logger.warning(f"Could not extract a clear response from agent. Full response: {agent_run_response!r}")
            return "I'm sorry, I wasn't able to formulate a response for that."

        except Exception as e:
            self.logger.error(f"Error running Calendar Agent: {e!s}", exc_info=True)
            # Depending on policy, you might raise e or return a user-friendly error message
            return f"I encountered an error trying to process your request: {e!s}"