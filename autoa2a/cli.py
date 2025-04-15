import click
import os
from jinja2 import Template

TEMPLATE_DIR = 'templates'  # Directory where the template files are stored
OUTPUT_DIR = '.'  # Output directory (current directory)

@click.group()
def autoa2a():
    """AutoA2A: A tool to scaffold A2A server agents"""
    pass

@click.command()
@click.option('--framework', type=str, default='langgraph', help='Framework name (e.g., langgraph, other)')
def init(framework):
    """Initialize a scaffold for A2A server."""
    try:
        if framework == "langgraph":
            template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'agent_specific', 'langgraph')
        else:
            raise ValueError(f"Unsupported framework: {framework}")

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
        click.echo("👉 Next steps: Update the agent import, input/output logic, and run the server.")
    
    except Exception as e:
        click.echo(f"❌ Error: {e}")

autoa2a.add_command(init)

if __name__ == '__main__':
    autoa2a()
