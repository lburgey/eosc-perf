import { Report, Result } from '../../api';
import { useQuery } from 'react-query';
import { getHelper } from '../../api-helpers';
import { LoadingOverlay } from '../loadingOverlay';
import React from 'react';

export function ResultReportInfo(props: { report: Report; token: string; refetch: () => void }) {
    let { isLoading, data, isSuccess } = useQuery(
        'result',
        () => {
            return getHelper<Result>('/results/' + props.report.resource_id);
        },
        {
            enabled: !!props.token,
            refetchOnWindowFocus: false, // do not spam queries
        }
    );

    return (
        <>
            {isLoading && <LoadingOverlay />}
            {isSuccess && data && (
                <p>
                    {/* TODO: *reporter* info */}
                    {/* Reported by: {{ reporter_name }} ({{ reporter_mail }})<br /> */}
                    Message: {props.report.message}
                    <br />
                    Date: {props.report.created_at}
                    <br />
                    Site: {data.data.site.name}
                    <br />
                    Benchmark: {data.data.benchmark.docker_image + data.data.benchmark.docker_tag}
                    <br />
                    {/* Uploader: {{ uploader_name }} ({{ uploader_mail }})<br /> */}
                    Tags: {data.data.tags.map((tag) => tag.name).join(', ')}
                    <br />
                    JSON:
                    <pre>
                        <code
                            className="json rounded"
                            style={{ overflow: 'scroll', maxHeight: '60vh' }}
                        >
                            {data.data.json}
                        </code>
                    </pre>
                </p>
            )}
        </>
    );
}
