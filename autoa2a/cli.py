import click
import os
from jinja2 import Template

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')  # Directory where the template files are stored
COMMON_TEMPLATE_DIR = os.path.join(TEMPLATE_DIR, 'common')
AGENT_SPECIFIC_TEMPLATE_DIR = os.path.join(TEMPLATE_DIR, 'agent_specific')
OUTPUT_DIR = '.'  # Output directory (current directory)

@click.group()
def autoa2a():
    """AutoA2A: A tool to scaffold A2A server agents"""
    pass

@click.command()
@click.option('--framework', type=str, default='langgraph', help='Framework name (e.g., langgraph, openai, llama-index, crewai, pydantic, other)')
def init(framework):
    """Initialize a scaffold for A2A server."""
    try:
        if framework in ["langgraph", "openai", "llama-index", "crewai", "pydantic"]:
            template_dir = os.path.join(AGENT_SPECIFIC_TEMPLATE_DIR, framework)
        else:
            raise ValueError(f"Unsupported framework: {framework}")
        
        for filename in os.listdir(COMMON_TEMPLATE_DIR):
            if filename.endswith(".jinja2"):
                template_path = os.path.join(COMMON_TEMPLATE_DIR, filename)
                output_filename = filename.replace(".jinja2", "")
                output_path = os.path.join(OUTPUT_DIR, output_filename)

                # Read and render the template
                with open(template_path, 'r') as f:
                    template_content = f.read()
                    template = Template(template_content)
                    rendered_content = template.render()

                # Write the rendered content to output
                with open(output_path, 'w') as out_f:
                    out_f.write(rendered_content)

                click.echo(f"✅ Created: {output_filename}")

        # Loop over all .jinja2 files and render them into the current folder
        for filename in os.listdir(template_dir):
            if filename.endswith(".jinja2"):
                template_path = os.path.join(template_dir, filename)
                output_filename = filename.replace(".jinja2", "")
                output_path = os.path.join(OUTPUT_DIR, output_filename)

                # Read and render the template
                with open(template_path, 'r') as f:
                    template_content = f.read()
                    template = Template(template_content)
                    rendered_content = template.render()

                # Write the rendered content to output
                with open(output_path, 'w') as out_f:
                    out_f.write(rendered_content)

                click.echo(f"✅ Created: {output_filename}")

        click.echo("\n🎉 A2A scaffold initialized in current directory.")
        click.echo("👉 Next steps: Follow the TODOs in the code to update the agent import, input/output logic, and run the server.")
        click.echo("👉 Run the server with `uv run .`")
    
    except Exception as e:
        click.echo(f"❌ Error: {e}")

autoa2a.add_command(init)

if __name__ == '__main__':
    autoa2a()
