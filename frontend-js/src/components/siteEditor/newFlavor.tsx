import { Site } from 'api';
import React, { useState } from 'react';
import { Button, ListGroup } from 'react-bootstrap';
import { FlavorSubmissionModal } from 'components/submissionModals/flavorSubmissionModal';

export function NewFlavor(props: { site: Site }) {
    const [showSubmitModal, setShowSubmitModal] = useState(false);

    return (
        <ListGroup.Item key="new-flavor">
            <Button variant="success" onClick={() => setShowSubmitModal(true)}>
                New
            </Button>
            <FlavorSubmissionModal
                show={showSubmitModal}
                onHide={() => setShowSubmitModal(false)}
                site={props.site}
            />
        </ListGroup.Item>
    );
}