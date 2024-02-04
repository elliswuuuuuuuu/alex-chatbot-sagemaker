// @ts-nocheck
import {
  Box,
  Button,
  Container,
  Form,
  FormField,
  Header,
  Input,
  SpaceBetween,
  Table,
  Tiles,
  Grid,
  Toggle,
} from '@cloudscape-design/components';
import { useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import useInput from 'src/hooks/useInput';
import useLsLanguageModelList from 'src/hooks/useLsLanguageModelList';
import useToggle from 'src/hooks/useToggle';
import { genRandomNum } from 'src/utils/genUID';

const SIZE = 'l';

const TYPE = { sagemaker: 'sagemaker_endpoint', thirdParty: 'third_party_api' };
const SAGEMAKER_MODEL_TYPE = [
  { label: 'non-llama2', value: 'non_llama2' },
  { label: 'llama2', value: 'llama2' },
];
const THIRD_PARTY_API_MODEL_TYPES = [
  { label: 'Bedrock', value: 'bedrock' },
  { label: 'Bedrock API', value: 'bedrock_api' },
  { label: 'LLM API', value: 'llm_api' },
];
const THIRD_PARTY_API_MODEL_NAMES = [
  { label: 'Baichuan2-53B', value: 'Baichuan2-53B', modelType: ['llm_api'] },
  { label: 'Baichuan2-192k', value: 'Baichuan2-192k', modelType: ['llm_api'] },
  {
    label: 'anthropic.claude-v2',
    value: 'anthropic.claude-v2',
    modelType: ['bedrock', 'bedrock_api'],
  },
  {
    label: 'anthropic.claude-v1',
    value: 'anthropic.claude-v1',
    modelType: ['bedrock', 'bedrock_api'],
  },
  {
    label: 'anthropic.claude-instant-v1',
    value: 'anthropic.claude-instant-v1',
    modelType: ['bedrock', 'bedrock_api'],
  },
  {
    label: 'meta.llama2-13b-chat-v1',
    value: 'meta.llama2-13b-chat-v1',
    modelType: ['bedrock', 'bedrock_api'],
  },
];

const LanguageModelStrategy = () => {
  const [strategyName, bindStrategyName, resetStrategyName] = useInput('');
  const [type, setType] = useState(TYPE.sagemaker);
  const [sagemakerEndpoint, bindSagemakerEndpoint, resetSagemakerEndpoint] =
    useInput('');
  const [
    isSagemakerStreaming,
    bindIsSagemakerStreaming,
    resetIsSagemakerStreaming,
  ] = useToggle(false);
  const [embeddingEndpoint, bindEmbeddingEndpoint, resetEmbeddingEndpoint] =
    useInput('');
  const [
    thirdPartyEmbeddingEndpoint,
    bindThirdPartyEmbeddingEndpoint,
    resetThirdPartyEmbeddingEmbeddingEndpoint,
  ] = useInput('');
  const [thirdPartyModelType, setThirdPartyModelType] = useState(
    THIRD_PARTY_API_MODEL_TYPES[0].value
  );
  const [sagemakerModelType, setSagemakerModelType] = useState(
    SAGEMAKER_MODEL_TYPE[0].value
  );
  const [thirdPartyModelNameOpts, setThirdPartyModelNameOpts] = useState(
    THIRD_PARTY_API_MODEL_NAMES
  );
  const [thirdPartyModelName, setThirdPartyModelName] = useState(
    THIRD_PARTY_API_MODEL_NAMES[0].value
  );

  const [thirdPartyApiUrl, bindThirdPartyApiUrl, resetThirdPartyApiUrl] =
    useInput('');
  const [thirdPartyApiKey, bindThirdPartyApiKey, resetThirdPartyApiKey] =
    useInput('');
  const [
    thirdPartySecretKey,
    bindThirdPartySecretKey,
    resetThirdPartySecretKey,
  ] = useInput('');

  const [validating, setValidating] = useState(false);

  useEffect(() => {
    const filteredModalNameOpts = THIRD_PARTY_API_MODEL_NAMES.filter((item) =>
      item.modelType.includes(thirdPartyModelType)
    );
    setThirdPartyModelName(filteredModalNameOpts[0].value);
    setThirdPartyModelNameOpts(filteredModalNameOpts);
    resetThirdPartyApiUrl();
    resetThirdPartyApiKey();
    resetThirdPartySecretKey();
  }, [thirdPartyModelType]);

  const [
    isCheckedTitanEmbedding,
    bindIsCheckedTitanEmbedding,
    resetTitanEmbedding,
  ] = useToggle(false);

  const [isCheckedLlama2Switch, bindLlama2Switch, resetLlama2Switch] =
    useToggle(false);

  useEffect(() => {
    if (isCheckedLlama2Switch) {
      setSagemakerModelType('llama2');
    } else {
      setSagemakerModelType('non_llama2');
    }
  }, [isCheckedLlama2Switch]);

  const resetForm = useCallback(() => {
    resetStrategyName();
    resetTitanEmbedding();
    resetSagemakerEndpoint();
    resetIsSagemakerStreaming();
    resetEmbeddingEndpoint();
    resetThirdPartyEmbeddingEmbeddingEndpoint();
    setThirdPartyModelType(THIRD_PARTY_API_MODEL_TYPES[0].value);
    resetLlama2Switch();
    setSagemakerModelType(SAGEMAKER_MODEL_TYPE[0].value);
    resetThirdPartyApiUrl();
    resetThirdPartyApiKey();
    resetThirdPartySecretKey();
    setValidating(false);
  }, []);

  const {
    lsLanguageModelList,
    lsAddLanguageModelItem,
    lsClearLanguageModelList,
    lsDelLanguageModelItem,
  } = useLsLanguageModelList();

  return (
    <SpaceBetween size={SIZE}>
      <SpaceBetween size="s">
        <Container
          header={<Header variant="h2">Language Model Strategies</Header>}
        >
          <SpaceBetween size={SIZE}>
            <Table
              items={lsLanguageModelList}
              variant="borderless"
              empty={
                <Box
                  margin={{ vertical: 'xs' }}
                  textAlign="center"
                  color="inherit"
                >
                  <SpaceBetween size="m">
                    <b>No resources</b>
                  </SpaceBetween>
                </Box>
              }
              columnDefinitions={[
                {
                  id: 'strategyName',
                  header: 'Strategy Name',
                  width: 90,
                  cell: (item) => item.strategyName,
                },
                {
                  id: 'modelName',
                  header: 'Model Name',
                  isRowHeader: true,
                  width: 150,
                  cell: (item) => item.modelName || 'n/a',
                },
                {
                  id: 'type',
                  header: 'Type',
                  width: 120,
                  cell: (item) => item.type,
                },
                {
                  id: 'modelType',
                  header: 'Model Type',
                  width: 50,
                  cell: (item) => item.modelType,
                },
                {
                  id: 'sagemakerEndpoint',
                  header: 'SageMaker Endpoint',
                  width: 200,
                  cell: (item) => item.sagemakerEndpoint || 'n/a',
                },
                {
                  id: 'embeddingEndpoint',
                  header: 'EmbeddingEndpoint',
                  width: 200,
                  cell: (item) => {
                    if (item.isCheckedTitanEmbedding)
                      return 'Use Titan Embedding';
                    return item.embeddingEndpoint || 'n/a';
                  },
                },
                {
                  id: 'apiUrl',
                  header: 'API URL',
                  width: 200,
                  cell: (item) => item.apiUrl || 'n/a',
                },
                {
                  id: 'apiKey',
                  header: 'API Key',
                  width: 200,
                  cell: (item) => item.apiKey || 'n/a',
                },
                {
                  id: 'secretKey',
                  header: 'Secret Key',
                  width: 200,
                  cell: (item) => item.secretKey || 'n/a',
                },
                {
                  id: 'operations',
                  header: 'Operations',
                  width: 20,
                  cell: (item) => (
                    <SpaceBetween size="xxs">
                      <Button
                        iconName="remove"
                        onClick={() => {
                          const bool = window?.confirm(
                            'Confirm to delete this language model strategy?'
                          );
                          if (bool) lsDelLanguageModelItem(item.recordId);
                        }}
                      />
                    </SpaceBetween>
                  ),
                },
              ]}
            />
            <Box float="right">
              <Button
                onClick={() => {
                  const bool = window?.confirm('Confirm to clear this list?');
                  if (bool) lsClearLanguageModelList();
                }}
              >
                Delete all language model strategies
              </Button>
            </Box>
          </SpaceBetween>
        </Container>
      </SpaceBetween>

      <Container
        header={<Header variant="h2">Create a language model strategy</Header>}
      >
        <form onSubmit={(e) => e.preventDefault()}>
          <Form
            variant="embedded"
            actions={
              <SpaceBetween alignItems="center" size={SIZE}>
                <Button
                  variant="primary"
                  iconName="status-positive"
                  onClick={() => {
                    setValidating(true);
                    if (!strategyName)
                      return toast.error('Please provide Strategy Name');

                    try {
                      let values;
                      if (type === TYPE.sagemaker) {
                        // SageMaker endpoint
                        values = {
                          strategyName,
                          type,
                          embeddingEndpoint,
                          modelType: sagemakerModelType,
                          recordId: `${sagemakerEndpoint}-${genRandomNum()}`,
                          isCheckedTitanEmbedding,
                          // *** different items
                          sagemakerEndpoint,
                          isSagemakerStreaming,
                        };
                      } else {
                        // Third Party APIs
                        values = {
                          strategyName,
                          type,
                          embeddingEndpoint: thirdPartyEmbeddingEndpoint,
                          modelType: thirdPartyModelType,
                          modelName: thirdPartyModelName,
                          recordId: `${thirdPartyModelName}-${genRandomNum()}`,
                          isCheckedTitanEmbedding,
                          // *** different items
                          apiUrl: thirdPartyApiUrl,
                          apiKey: thirdPartyApiKey,
                          secretKey: thirdPartySecretKey,
                        };
                      }
                      lsAddLanguageModelItem(values);
                      resetForm();
                    } catch (error) {
                      console.error(error);
                    } finally {
                      setValidating(false);
                    }
                  }}
                >
                  Confirm
                </Button>
              </SpaceBetween>
            }
          >
            <SpaceBetween size={SIZE}>
              <FormField
                stretch
                label="Strategy Name"
                errorText={
                  validating && !strategyName && 'Please provide Strategy Name'
                }
              >
                <Input
                  {...bindStrategyName}
                  placeholder="Please provide a name for this language model strategy"
                />
              </FormField>
              <FormField stretch label="Please select the endpoint type">
                <Tiles
                  value={type}
                  onChange={(e) => setType(e.detail.value)}
                  items={[
                    {
                      value: TYPE.sagemaker,
                      label: 'SageMaker Endpoint',
                      description:
                        'Deployed service for real-time ML model inference',
                    },
                    {
                      value: TYPE.thirdParty,
                      label: 'Third Party APIs',
                      description: 'Options are Bedrock, Claude, ChatGLM etc.',
                    },
                  ]}
                />
              </FormField>

              {type === TYPE.sagemaker ? (
                <>
                  <FormField>
                    <Toggle {...bindLlama2Switch}>
                      LLama2 model deployed through Jumpstart
                    </Toggle>
                  </FormField>
                  {/* <FormField label="Model Type">
                    <Tiles
                      columns={4}
                      onChange={({ detail }) =>
                        setSagemakerModelType(detail.value)
                      }
                      value={sagemakerModelType}
                      items={SAGEMAKER_MODEL_TYPE}
                    />
                  </FormField> */}
                  <Grid gridDefinition={[{ colspan: 8 }, { colspan: 4 }]}>
                    <FormField stretch label="SageMaker Endpoint">
                      <Input
                        {...bindSagemakerEndpoint}
                        placeholder="Please provide SageMaker Endpoint"
                      />
                    </FormField>
                    <FormField label="Switch for Streaming">
                      <Toggle {...bindIsSagemakerStreaming}>Streaming</Toggle>
                    </FormField>
                  </Grid>
                  <FormField>
                    <Toggle {...bindIsCheckedTitanEmbedding}>
                      Use Titan Embedding
                    </Toggle>
                  </FormField>
                  {isCheckedTitanEmbedding ? null : (
                    <FormField label="Embedding Endpoint">
                      <Input
                        {...bindEmbeddingEndpoint}
                        placeholder="Please provide embedding endpoint"
                      />
                    </FormField>
                  )}
                </>
              ) : (
                <>
                  <FormField label="Model Type" stretch>
                    <Tiles
                      columns={4}
                      onChange={({ detail }) =>
                        setThirdPartyModelType(detail.value)
                      }
                      value={thirdPartyModelType}
                      items={THIRD_PARTY_API_MODEL_TYPES}
                    />
                  </FormField>
                  <FormField label="Model Name" stretch>
                    <Tiles
                      columns={4}
                      onChange={({ detail }) =>
                        setThirdPartyModelName(detail.value)
                      }
                      value={thirdPartyModelName}
                      items={thirdPartyModelNameOpts}
                    />
                  </FormField>
                  <FormField>
                    <Toggle {...bindIsCheckedTitanEmbedding}>
                      Use Titan Embedding
                    </Toggle>
                  </FormField>
                  {isCheckedTitanEmbedding ? null : (
                    <FormField label="Embedding Endpoint">
                      <Input
                        {...bindThirdPartyEmbeddingEndpoint}
                        placeholder="Please provide embedding endpoint"
                      />
                    </FormField>
                  )}
                  {thirdPartyModelType ===
                  'bedrock' ? null : thirdPartyModelType === 'bedrock_api' ? (
                    <>
                      <FormField label="API URL">
                        <Input
                          {...bindThirdPartyApiUrl}
                          placeholder="Please provide API URL"
                        />
                      </FormField>
                    </>
                  ) : thirdPartyModelType === 'llm_api' ? (
                    <>
                      <FormField label="API URL">
                        <Input
                          {...bindThirdPartyApiUrl}
                          placeholder="Please provide API URL"
                        />
                      </FormField>
                      <FormField label="API Key">
                        <Input
                          {...bindThirdPartyApiKey}
                          placeholder="Please provide API Key"
                        />
                      </FormField>
                      <FormField label="Secret Key">
                        <Input
                          {...bindThirdPartySecretKey}
                          placeholder="Please provide Secret Key"
                        />
                      </FormField>
                    </>
                  ) : null}
                </>
              )}
            </SpaceBetween>
          </Form>
        </form>
      </Container>
    </SpaceBetween>
  );
};

export default LanguageModelStrategy;
