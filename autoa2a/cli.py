import click
import os
from jinja2 import Template
import yaml

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')  # Directory where the template files are stored
COMMON_TEMPLATE_DIR = os.path.join(TEMPLATE_DIR, 'common')
AGENT_SPECIFIC_TEMPLATE_DIR = os.path.join(TEMPLATE_DIR, 'agent_specific')
OUTPUT_DIR = '.'  # Output directory (current directory)

@click.group()
def autoa2a():
    """AutoA2A: A tool to scaffold A2A server agents"""
    pass

def load_framework_dependencies(framework):
    """Load framework-specific dependencies from YAML file"""
    deps_path = os.path.join(TEMPLATE_DIR, 'framework_dependencies.yaml')
    try:
        with open(deps_path, 'r') as f:
            all_deps = yaml.safe_load(f)
            return all_deps.get('frameworks', {}).get(framework, [])
    except Exception as e:
        click.echo(f"Warning: Could not load framework dependencies: {e}")
        return []

@click.command()
@click.option('--framework', type=str, default='langgraph', help='Framework name (e.g., langgraph, openai, llama-index, crewai, pydantic, other)')
def init(framework):
    """Initialize a scaffold for A2A server."""
    try:
        if framework in ["langgraph", "openai", "llama-index", "crewai", "pydantic"]:
            template_dir = os.path.join(AGENT_SPECIFIC_TEMPLATE_DIR, framework)
        else:
            raise ValueError(f"Unsupported framework: {framework}")
        

        # render pyproject.toml if it doesn't exist
        pyproject_template_path = os.path.join(COMMON_TEMPLATE_DIR, 'pyproject.toml.jinja2')
        pyproject_output_path = os.path.join(OUTPUT_DIR, 'pyproject.toml')
        framework_dependencies = load_framework_dependencies(framework)
        if not os.path.exists(pyproject_output_path):
            name = "autoa2a-agent"
            description = "An A2A server agent"
            with open(pyproject_template_path, 'r') as f:
                template_content = f.read()
                template = Template(template_content)
                rendered_content = template.render(
                    project_name=name,
                    description=description,
                    framework=framework,
                    framework_dependencies=framework_dependencies
                )
            with open(pyproject_output_path, 'w') as out_f:
                out_f.write(rendered_content)
            click.echo(f"✅ Created: pyproject.toml")
        else:
            click.echo(f"👉 pyproject.toml already exists in {OUTPUT_DIR}")
        
        for filename in os.listdir(COMMON_TEMPLATE_DIR):
            if filename.endswith(".jinja2"):
                if filename == "pyproject.toml.jinja2":
                    continue
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
