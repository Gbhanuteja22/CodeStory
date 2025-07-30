from pocketflow import Flow
from documentation_processors import (
    CodebaseRetriever,
    ConceptIdentifier,
    RelationshipAnalyzer,
    ChapterOrganizer,
    ContentGenerator,
    DocumentationAssembler
)

class DocumentationWorkflow:
    def __init__(self):
        self.processing_pipeline = None
        
    def create_processing_pipeline(self):
        codebase_retriever = CodebaseRetriever()
        concept_identifier = ConceptIdentifier(max_retries=5, wait=20)
        relationship_analyzer = RelationshipAnalyzer(max_retries=5, wait=20)
        chapter_organizer = ChapterOrganizer(max_retries=5, wait=20)
        content_generator = ContentGenerator(max_retries=5, wait=20)
        documentation_assembler = DocumentationAssembler()
        
        codebase_retriever >> concept_identifier
        concept_identifier >> relationship_analyzer
        relationship_analyzer >> chapter_organizer
        chapter_organizer >> content_generator
        content_generator >> documentation_assembler
        
        self.processing_pipeline = Flow(start=codebase_retriever)
        return self.processing_pipeline
        
    def execute(self, workspace_configuration):
        pipeline = self.create_processing_pipeline()
        pipeline.run(workspace_configuration)
        return workspace_configuration
