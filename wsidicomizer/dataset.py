import copy
from typing import Callable, List

import pydicom
from highdicom.content import (IssuerOfIdentifier, SpecimenCollection,
                               SpecimenDescription, SpecimenPreparationStep,
                               SpecimenSampling, SpecimenStaining)
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence as DicomSequence
from pydicom.uid import UID as Uid
from wsidicom.conceptcode import (SpecimenEmbeddingMediaCode,
                                  SpecimenFixativesCode,
                                  SpecimenPreparationProcedureCode,
                                  SpecimenStainsCode)


def get_image_type(image_flavor: str, level_index: int) -> List[str]:
    """Return image type.

    Parameters
    ----------
    image_flavor: str
        Image flavor ('VOLUME', 'LABEL', 'OVERVIEW')
    level_index: int:
        Pyramidal level index of the image.

    Returns
    ----------
    List[str]
        Image type.
    """
    if image_flavor == 'VOLUME' and level_index == 0:
        resampled = 'NONE'
    else:
        resampled = 'RESAMPLED'

    return ['ORGINAL', 'PRIMARY', image_flavor, resampled]


def create_wsi_dataset(
    uid_generator: Callable[..., Uid] = pydicom.uid.generate_uid
) -> Dataset:
    """Return minimal base dataset.

    Parameters
    ----------
    uid_generator: Callable[..., Uid]
        Function that can generate Uids.

    Returns
    ----------
    Dataset
        Minimal WSI dataset.
    """
    dataset = Dataset()
    dataset.StudyInstanceUID = uid_generator()
    dataset.SeriesInstanceUID = uid_generator()
    dataset.FrameOfReferenceUID = uid_generator()
    dataset.Modality = 'SM'
    dataset.SOPClassUID = '1.2.840.10008.5.1.4.1.1.77.1.6'

    # Generic dimension organization sequence
    dimension_organization_uid = uid_generator()
    dimension_organization_sequence = Dataset()
    dimension_organization_sequence.DimensionOrganizationUID = (
        dimension_organization_uid
    )
    dataset.DimensionOrganizationSequence = DicomSequence(
        [dimension_organization_sequence]
    )

    # Generic dimension index sequence
    dimension_index_sequence = Dataset()
    dimension_index_sequence.DimensionOrganizationUID = (
        dimension_organization_uid
    )
    dimension_index_sequence.DimensionIndexPointer = (
        pydicom.tag.Tag('PlanePositionSlideSequence')
    )
    dataset.DimensionIndexSequence = DicomSequence(
        [dimension_index_sequence]
    )

    dataset.BurnedInAnnotation = 'NO'
    dataset.SpecimenLabelInImage = 'NO'
    dataset.VolumetricProperties = 'VOLUME'
    return dataset


def create_device_module(
    manufacturer: str = None,
    model_name: str = None,
    serial_number: str = None,
    software_versions: List[str] = None
) -> Dataset:
    dataset = Dataset()
    properties = {
        'Manufacturer': manufacturer,
        'ManufacturerModelName': model_name,
        'DeviceSerialNumber': serial_number,
        'SoftwareVersions': software_versions
    }
    for name, value in properties.items():
        if value is not None:
            setattr(dataset, name, value)
    return dataset


def create_simple_sample(
    sample_id: str,
    embedding_medium: str = None,
    fixative: str = None,
    stainings: List[str] = None,
    uid_generator: Callable[..., Uid] = pydicom.uid.generate_uid
) -> Dataset:
    if embedding_medium is not None:
        embedding_medium_code = (
            SpecimenEmbeddingMediaCode(embedding_medium).code
        )
    else:
        embedding_medium_code = None
    if fixative is not None:
        fixative_code = SpecimenFixativesCode(fixative).code
    else:
        fixative_code = None
    if stainings is not None:
        processing_type = SpecimenPreparationProcedureCode('Staining').code
        processing_procedure = SpecimenStaining([
            SpecimenStainsCode(staining).code for staining in stainings
        ])
        sample_preparation_step = SpecimenPreparationStep(
            specimen_id=sample_id,
            processing_type=processing_type,
            processing_procedure=processing_procedure,
            embedding_medium=embedding_medium_code,
            fixative=fixative_code
        )
        sample_preparation_steps = [sample_preparation_step]
    else:
        sample_preparation_steps = None

    specimen = SpecimenDescription(
        specimen_id=sample_id,
        specimen_uid=uid_generator(),
        specimen_preparation_steps=sample_preparation_steps
    )
    return specimen


def create_simple_specimen_module(
    slide_id: str,
    samples: List[Dataset]
) -> Dataset:
    # Generic specimen sequence
    dataset = Dataset()
    dataset.ContainerIdentifier = slide_id

    container_type_code_sequence = Dataset()
    container_type_code_sequence.CodeValue = '258661006'
    container_type_code_sequence.CodingSchemeDesignator = 'SCT'
    container_type_code_sequence.CodeMeaning = 'Slide'
    dataset.ContainerTypeCodeSequence = (
        DicomSequence([container_type_code_sequence])
    )

    container_component_sequence = Dataset()
    container_component_sequence.ContainerComponentMaterial = 'GLASS'
    container_component_type_code_sequence = Dataset()
    container_component_type_code_sequence.CodeValue = '433472003'
    container_component_type_code_sequence.CodingSchemeDesignator = 'SCT'
    container_component_type_code_sequence.CodeMeaning = (
        'Microscope slide coverslip'
    )
    container_component_sequence.ContainerComponentTypeCodeSequence = (
        DicomSequence([container_component_type_code_sequence])
    )
    dataset.ContainerComponentSequence = (
        DicomSequence([container_component_sequence])
    )
    specimen_description_sequence = (
        DicomSequence(samples)
    )
    dataset.SpecimenDescriptionSequence = specimen_description_sequence

    return dataset


def create_generic_optical_path_module() -> Dataset:
    dataset = Dataset()
    # Generic optical path sequence
    optical_path_sequence = Dataset()
    optical_path_sequence.OpticalPathIdentifier = '0'
    illumination_type_code_sequence = Dataset()
    illumination_type_code_sequence.CodeValue = '111744'
    illumination_type_code_sequence.CodingSchemeDesignator = 'DCM'
    illumination_type_code_sequence.CodeMeaning = (
        'Brightfield illumination'
    )
    optical_path_sequence.IlluminationTypeCodeSequence = DicomSequence(
        [illumination_type_code_sequence]
    )
    illumination_color_code_sequence = Dataset()
    illumination_color_code_sequence.CodeValue = 'R-102C0'
    illumination_color_code_sequence.CodingSchemeDesignator = 'SRT'
    illumination_color_code_sequence.CodeMeaning = 'Full Spectrum'
    optical_path_sequence.IlluminationColorCodeSequence = DicomSequence(
        [illumination_color_code_sequence]
    )
    dataset.OpticalPathSequence = DicomSequence([optical_path_sequence])

    return dataset


def create_test_base_dataset(
    uid_generator: Callable[..., Uid] = pydicom.uid.generate_uid
) -> Dataset:
    """Return simple base dataset for testing.

    Parameters
    ----------
    uid_generator: Callable[..., Uid]
        Function that can generate Uids.

    Returns
    ----------
    Dataset
        Common dataset.
    """
    dataset = create_wsi_dataset(uid_generator)

    # Generic device module
    dataset.update(create_device_module(
        'Scanner manufacturer',
        'Scanner model name',
        'Scanner serial number',
        ['Scanner software versions']
    ))

    # Generic specimen module
    dataset.update(create_simple_specimen_module(
        'slide id',
        samples=[create_simple_sample(
            'sample id',
            uid_generator=uid_generator
        )]
    ))

    # Generic optical path sequence
    dataset.update(create_generic_optical_path_module())

    return dataset
