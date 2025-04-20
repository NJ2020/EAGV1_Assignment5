import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
# from google import genai
import google.generativeai as genai
from concurrent.futures import TimeoutError
from functools import partial
from PromptEvaluator import evaluate_promt

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")

# Added by NJ -- START
# # Set your API key
genai.configure(api_key=api_key)
# Create a model instance
client = genai.GenerativeModel("gemini-2.0-flash")

# Generate content
# response = model.generate_content("Tell me a joke.")

# Added by NJ -- END

# client = genai.Client(api_key=api_key)


max_iterations = 2
last_response = None
iteration = 0
iteration_response = []

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.generate_content(
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["example2_Neeresh.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                print('\n-------- TOOLS LIST --------------\n')
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                # print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:
                    # First, let's inspect what a tool object looks like
                    # if tools:
                    #     print(f"First tool properties: {dir(tools[0])}")
                    #     print(f"First tool example: {tools[0]}")
                    
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    # print("1111111111111100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
                    print("Successfully created tools description",tools_description)
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                system_prompt = f"""You are an agent working with Microsoft Paint in iterations. You have access to various Microsoft Paint tools. """

                query = """ 

                    Your task is to follow the step-by-step plan below to accomplish the goal. Think carefully before each step, explain your reasoning, identify the type of reasoning being used, and use tools as needed.

                    Goal:
                    Step 1: Open Microsoft Paint.  
                    Step 2: Add text 'INDIA' in Opened Paint App.

                    Available tools:
                    {tools_description}

                    You must follow this reasoning and response format for each step:
                    1. Step Reasoning: [Brief explanation of why and what you're doing]
                    2. Reasoning Type: [e.g., lookup, tool-use, spatial reasoning, sequencing]
                    3. Tool Decision: [if using a tool, state which one and what parameters it needs]
                    4. Self-Check: [verify input/output validity or sanity check]
                    5. Response Line (MUST be ONE line, NO other text):
                    FUNCTION_CALL: function_name|param1|param2|...
                    FINAL_ANSWER: [string value returned by the function call]
                    6. If uncertain or if a tool fails (Error Handling or Fallbacks), use:
                    - FUNCTION_CALL: report_error|[describe issue briefly]

                    Examples:
                    - FUNCTION_CALL: draw_rectangle|10|50|10|50
                    - FUNCTION_CALL: add_text_in_paint|INDIA
                    - FINAL_ANSWER: open_paint function called successfully....1111
                    - FUNCTION_CALL: report_error|Unable to locate rectangle area

                    Important Instructions:
                    - Proceed step-by-step, one action per turn.
                    - Do not skip steps or assume outcomes.
                    - Do not include any explanation outside of the prescribed format.
                    - Responses outside the "Response Line" will be ignored.

                """
                # print("query is:11111", query)

                # NJ: Before Function Calling via MCP Server, lets evaluate the prompt
                print(f"\n--------- EVALUATING PROMPT ---------")
                print("PROMPT EValuation is: ", evaluate_promt(system_prompt + query))

                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response
                
                while iteration < max_iterations:
                    print(f"\n------- Iteration {iteration + 1} -------")


                    if last_response is None:
                        current_query = query
                    else:
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"

                    # print("current_query is:11111", query)

                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    
                    # print("Debug Statement - The PROMPT is:", prompt)

                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        # print(f"LLM Response: {response_text}")
                        
                        # Find the FUNCTION_CALL line in the response
                        for line in response_text.split('\n'):
                            line = line.strip()
                            # print(f"line in response_text1: {line}")
                            
                            if line.startswith("FUNCTION_CALL:"):
                                response_text = line
                                break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break


                    if response_text.startswith("FUNCTION_CALL:"):
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        
                        print(f"\nDEBUG: Raw function info: {function_info}")
                        print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            print(f"DEBUG: Schema properties: {schema_properties}")

                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    raise ValueError(f"Not enough parameters provided for {func_name}")
                                    
                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')
                                
                                print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    # Handle array input
                                    if isinstance(value, str):
                                        value = value.strip('[]').split(',')
                                    arguments[param_name] = [int(x.strip()) for x in value]
                                else:
                                    arguments[param_name] = str(value)

                            print(f"DEBUG: Final arguments: {arguments}")
                            print(f"DEBUG: Calling tool {func_name}")
                            
                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Raw result: {result}")
                            
                            # Get the full result content
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                print(f"DEBUG: Result has no content attribute")
                                iteration_result = str(result)
                                
                            print(f"DEBUG: Final iteration result: {iteration_result}")
                            
                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
                            iteration_response.append(
                                f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                f"and the function returned {result_str}."
                            )
                            last_response = iteration_result

                        except Exception as e:
                            print(f"DEBUG: Error details: {str(e)}")
                            print(f"DEBUG: Error type: {type(e)}")
                            import traceback
                            traceback.print_exc()
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break

                    elif response_text.startswith("FINAL_ANSWER:"):
                        print("\n=== Agent Execution Complete ===")
                       # result = await session.call_tool("open_paint")
                       # print(result.content[0].text)
                        # Wait longer for Paint to be fully maximized
                        await asyncio.sleep(1)

                        # Draw a rectangle
                        # result = await session.call_tool(
                        #     "draw_rectangle",
                        #     arguments={
                        #         "x1": 780,
                        #         "y1": 380,
                        #         "x2": 1140,
                        #         "y2": 700
                        #     }
                        # )
                        #print(result.content[0].text)

                        # Draw rectangle and add text
                        # result = await session.call_tool(
                        #     "add_text_in_paint",
                        #     arguments={
                        #         "text": response_text
                        #     }
                        # )
                        # print(result.content[0].text)
                        break

                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    
