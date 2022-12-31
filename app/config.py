import pathlib
import re

from environs import Env
from flask_babel import gettext as _
from kerko import codecs, extractors, transformers
from kerko.composer import Composer
from kerko.specs import CollectionFacetSpec, FieldSpec
from whoosh.fields import STORED

from .transformers import extra_field_cleaner

env = Env()  # pylint: disable=invalid-name
env.read_env()


class Config():
    app_dir = pathlib.Path(env.str('FLASK_APP')).parent.absolute()

    # Get configuration values from the environment.
    SECRET_KEY = env.str('SECRET_KEY')
    KERKO_ZOTERO_API_KEY = env.str('KERKO_ZOTERO_API_KEY')
    KERKO_ZOTERO_LIBRARY_ID = env.str('KERKO_ZOTERO_LIBRARY_ID')
    KERKO_ZOTERO_LIBRARY_TYPE = env.str('KERKO_ZOTERO_LIBRARY_TYPE')
    KERKO_DATA_DIR = env.str('KERKO_DATA_DIR', str(app_dir / 'data' / 'kerko'))

    # Set other configuration variables.
    LOGGING_HANDLER = 'default'
    EXPLAIN_TEMPLATE_LOADING = False

    LIBSASS_INCLUDES = [
        str(pathlib.Path(__file__).parent.parent / 'static' / 'src' / 'vendor' / 'bootstrap' / 'scss'),
        str(pathlib.Path(__file__).parent.parent / 'static' / 'src' / 'vendor' / '@fortawesome' / 'fontawesome-free' / 'scss'),
    ]

    BABEL_DEFAULT_LOCALE = 'en_GB'
    KERKO_WHOOSH_LANGUAGE = 'en'
    KERKO_ZOTERO_LOCALE = 'en-GB'

    HOME_URL = 'https://tech.eved.io'
    HOME_TITLE = _("Technology in Education")
    # HOME_SUBTITLE = _("...")

    NAV_TITLE = _("Library")
    KERKO_TITLE = _("Library")

    KERKO_PRINT_ITEM_LINK = True
    KERKO_PRINT_CITATIONS_LINK = True
    KERKO_RESULTS_FIELDS = ['id', 'attachments', 'bib', 'coins', 'data', 'preview', 'url']
    KERKO_RESULTS_ABSTRACTS = True
    KERKO_RESULTS_ABSTRACTS_MAX_LENGTH = 500
    KERKO_RESULTS_ABSTRACTS_MAX_LENGTH_LEEWAY = 40
    KERKO_TEMPLATE_BASE = 'app/base.html.jinja2'
    KERKO_TEMPLATE_LAYOUT = 'app/layout.html.jinja2'
    KERKO_TEMPLATE_SEARCH = 'app/search.html.jinja2'
    KERKO_TEMPLATE_SEARCH_ITEM = 'app/search-item.html.jinja2'
    KERKO_TEMPLATE_ITEM = 'app/item.html.jinja2'
    KERKO_DOWNLOAD_ATTACHMENT_NEW_WINDOW = True
    KERKO_RELATIONS_INITIAL_LIMIT = 50

    # CAUTION: The URL's query string must be changed after any edit to the CSL
    # style, otherwise zotero.org might still use a previously cached version of
    # the file.
    KERKO_CSL_STYLE = 'https://docs.edtechhub.org/static/dist/csl/eth_apa.xml?202012301815'

    KERKO_COMPOSER = Composer(
        whoosh_language=KERKO_WHOOSH_LANGUAGE,
        exclude_default_facets=['facet_tag', 'facet_link', 'facet_item_type'],
        exclude_default_fields=['data'],
        default_child_include_re='^(_publish|publishPDF)$',
        default_child_exclude_re='',
    )

    # Replace the default 'data' extractor to strip unwanted data from the Extra field.
    KERKO_COMPOSER.add_field(
        FieldSpec(
            key='data',
            field_type=STORED,
            extractor=extractors.TransformerExtractor(
                extractor=extractors.RawDataExtractor(),
                transformers=[extra_field_cleaner]
            ),
            codec=codecs.JSONFieldCodec()
        )
    )

    # Add field for storing the formatted item preview used on search result
    # pages. This relies on the CSL style's in-text citation formatting and only
    # makes sense using our custom CSL style!
    KERKO_COMPOSER.add_field(
        FieldSpec(
            key='preview',
            field_type=STORED,
            extractor=extractors.TransformerExtractor(
                extractor=extractors.ItemExtractor(key='citation', format_='citation'),
                # Zotero wraps the citation in a <span> element (most probably
                # because it expects the 'citation' format to be used in-text),
                # but that <span> has to be removed because our custom CSL style
                # causes <div>s to be nested within. Let's replace that <span>
                # with the same markup that the 'bib' format usually provides.
                transformers=[
                    lambda value: re.sub(r'^<span>', '<div class="csl-entry">', value, count=1),
                    lambda value: re.sub(r'</span>$', '</div>', value, count=1),
                ]
            )
        )
    )

    # Add extractors for the 'alternateId' field.
    # KERKO_COMPOSER.fields['alternateId'].extractor.extractors.append(
    #     extractors.TransformerExtractor(
    #         extractor=extractors.ItemDataExtractor(key='extra'),
    #         transformers=[
    #             transformers.find(
    #                 regex=r'^\s*EdTechHub.ItemAlsoKnownAs\s*:\s*(.*)$',
    #                 flags=re.IGNORECASE | re.MULTILINE,
    #                 max_matches=1,
    #             ),
    #             transformers.split(sep=';'),
    #         ]
    #     )
    # )
    # KERKO_COMPOSER.fields['alternateId'].extractor.extractors.append(
    #     extractors.TransformerExtractor(
    #         extractor=extractors.ItemDataExtractor(key='extra'),
    #         transformers=[
    #             transformers.find(
    #                 regex=r'^\s*KerkoCite.ItemAlsoKnownAs\s*:\s*(.*)$',
    #                 flags=re.IGNORECASE | re.MULTILINE,
    #                 max_matches=1,
    #             ),
    #             transformers.split(sep=' '),
    #         ]
    #     )
    # )
    # KERKO_COMPOSER.fields['alternateId'].extractor.extractors.append(
    #     extractors.TransformerExtractor(
    #         extractor=extractors.ItemDataExtractor(key='extra'),
    #         transformers=[
    #             transformers.find(
    #                 regex=r'^\s*shortDOI\s*:\s*(\S+)\s*$',
    #                 flags=re.IGNORECASE | re.MULTILINE,
    #                 max_matches=0,
    #             ),
    #         ]
    #     )
    # )
    
    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_outcome_measure',
            filter_key='outcome_measure',
            title=_('Outcome measure'),
            weight=10,
            collection_key='GM79T584',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_instructional_domain',
            filter_key='instructional_domain',
            title=_('Instructional domain (subject)'),
            weight=20,
            collection_key='WS8W94SN',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_education_level_and_type',
            filter_key='education_level_and_type',
            title=_('Education Level and Type'),
            weight=30,
            collection_key='R23G8DWQ',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_groups',
            filter_key='groups',
            title=_('Groups of students'),
            weight=40,
            collection_key='HFUWZ2HG',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_school_or_home',
            filter_key='school_or_home',
            title=_('School or home'),
            weight=50,
            collection_key='7EUZ6F5B',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_moderating_variables',
            filter_key='moderating_variables',
            title=_('Moderating variables'),
            weight=60,
            collection_key='TGF48A5K',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_tech_hardware',
            filter_key='tech_hardware',
            title=_('Tech Hardware'),
            weight=70,
            collection_key='54D5S6B4',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_tech_software',
            filter_key='tech_software',
            title=_('Tech Software'),
            weight=80,
            collection_key='XU6BVKWJ',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_tech_mechanism',
            filter_key='tech_mechanism',
            title=_('Tech mechanism'),
            weight=90,
            collection_key='39GD6S2M',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_learning_approach',
            filter_key='learning_approach',
            title=_('Learning Approach'),
            weight=100,
            collection_key='PHCF769D',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_teacher_pedagogy',
            filter_key='teacher_pedagogy',
            title=_('Teacher Pedagogy'),
            weight=110,
            collection_key='TPADRUD7',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_research_methods',
            filter_key='research_methods',
            title=_('Research methods'),
            weight=120,
            collection_key='TMBGUV3T',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_effect_size',
            filter_key='effect_size',
            title=_('Effect size/ heterogeneity'),
            weight=130,
            collection_key='H8KRJNSQ',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_hic_lmic',
            filter_key='hic_lmic',
            title=_('HIC/LMIC'),
            weight=140,
            collection_key='6MMPBGS9',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_quality_of_research',
            filter_key='quality_of_research',
            title=_('Quality of research'),
            weight=150,
            collection_key='4U3VJWPN',
        )
    )

    KERKO_COMPOSER.add_facet(
        CollectionFacetSpec(
            key='facet_geography_specific',
            filter_key='geography_specific',
            title=_('Geography if specific'),
            weight=160,
            collection_key='R4EJQDKR',
        )
    )


class DevelopmentConfig(Config):
    CONFIG = 'development'
    DEBUG = True
    ASSETS_DEBUG = env.bool('ASSETS_DEBUG', True)  # Don't bundle/minify static assets.
    KERKO_ZOTERO_START = env.int('KERKO_ZOTERO_START', 0)
    KERKO_ZOTERO_END = env.int('KERKO_ZOTERO_END', 0)
    LIBSASS_STYLE = 'expanded'
    LOGGING_LEVEL = env.str('LOGGING_LEVEL', 'DEBUG')


class ProductionConfig(Config):
    CONFIG = 'production'
    DEBUG = False
    ASSETS_DEBUG = env.bool('ASSETS_DEBUG', False)
    ASSETS_AUTO_BUILD = False
    LOGGING_LEVEL = env.str('LOGGING_LEVEL', 'WARNING')
    GOOGLE_ANALYTICS_ID = ''
    LIBSASS_STYLE = 'compressed'


CONFIGS = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}